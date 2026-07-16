#!/usr/bin/env python3
"""Create a one-run HTTPS smart-Git remote for current Guru candidate bytes."""

from __future__ import annotations

import argparse
import hashlib
import http.server
import os
import re
import secrets
import shutil
import signal
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any


_OFFICIAL_SOURCE_PATTERN = re.compile(
    r"^https://127\.0\.0\.1:(?P<port>[1-9][0-9]*)/org/"
    r"guru-fixture#(?P<tag>[A-Za-z0-9][A-Za-z0-9._-]*)$"
)


class HermeticFixtureInvalid(RuntimeError):
    pass


class _ParentSignalReceived(BaseException):
    def __init__(self, signum: int):
        super().__init__(f"fixture parent received signal {signum}")
        self.signum = signum


class _SignalTrap:
    def __init__(self) -> None:
        self.received: int | None = None

    def __call__(self, signum: int, _frame: Any) -> None:
        if self.received is None:
            self.received = signum
            raise _ParentSignalReceived(signum)


def validate_official_source(source: str) -> tuple[int, str]:
    """Accept only the pinned source shape understood by official 0.6.7."""
    match = _OFFICIAL_SOURCE_PATTERN.fullmatch(source)
    if match is None:
        raise HermeticFixtureInvalid(
            "official source must be a pinned hermetic HTTPS smart-Git repository whose root is guru-template"
        )
    port = int(match.group("port"))
    if port > 65535:
        raise HermeticFixtureInvalid("official HTTPS source port is invalid")
    return port, match.group("tag")


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[Any]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=60,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        stderr = getattr(error, "stderr", b"")
        if isinstance(stderr, bytes):
            detail = stderr.decode("utf-8", errors="replace").strip()
        else:
            detail = str(stderr).strip()
        raise HermeticFixtureInvalid(
            f"command failed: {' '.join(command)}{': ' + detail if detail else ''}"
        ) from error


def _hash_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, byteorder="big", signed=False))
    digest.update(value)


def _tree_digest(root: Path, *, ignore_checkout_git: bool = False) -> str:
    if root.is_symlink() or not root.exists() or not root.is_dir():
        raise HermeticFixtureInvalid(f"candidate source root is invalid: {root}")
    canonical = root.resolve(strict=True)
    digest = hashlib.sha256()
    _hash_field(digest, b"guru-https-fixture-tree-v1")
    for path in sorted(canonical.rglob("*"), key=lambda item: item.as_posix()):
        relative_path = path.relative_to(canonical)
        if ignore_checkout_git and relative_path.parts[0] == ".git":
            continue
        if path.is_symlink():
            raise HermeticFixtureInvalid(f"candidate source contains symlink: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise HermeticFixtureInvalid(f"candidate source contains non-regular entry: {path}")
        relative = relative_path.as_posix().encode("utf-8")
        _hash_field(digest, relative)
        _hash_field(digest, path.read_bytes())
    return digest.hexdigest()


def _remove_fixture_root(root: Path) -> None:
    shutil.rmtree(root)


def _install_signal_trap(trap: _SignalTrap) -> dict[int, Any]:
    previous: dict[int, Any] = {}
    for signum in (signal.SIGTERM, signal.SIGINT):
        previous[signum] = signal.getsignal(signum)
        signal.signal(signum, trap)
    return previous


def _restore_signal_handlers(previous: dict[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _wait_for_process_group_exit(
    process: subprocess.Popen[Any],
    process_group: int,
    timeout: float,
) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        process.poll()
        if not _process_group_exists(process_group):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)


def _terminate_child_process_group(
    process: subprocess.Popen[Any],
    process_group: int,
    original_signal: int,
) -> tuple[str, ...]:
    failures: list[str] = []
    for signum in (original_signal, signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process_group, signum)
        except ProcessLookupError:
            process.poll()
            return tuple(failures)
        except OSError as error:
            failures.append(f"cannot signal child process group {process_group} with {signum}: {error}")
        if _wait_for_process_group_exit(process, process_group, 1.0):
            return tuple(failures)
    failures.append(f"child process group {process_group} survived SIGKILL")
    return tuple(failures)


def _redeliver_parent_signal(signum: int) -> None:
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)
    raise RuntimeError(f"default signal disposition did not terminate process for signal {signum}")


class _GitHttpServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], repository_root: Path, request_log: list[str]):
        super().__init__(address, _GitHttpHandler)
        self.repository_root = repository_root
        self.request_log = request_log


class _GitHttpHandler(http.server.BaseHTTPRequestHandler):
    server: _GitHttpServer
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self._serve_git()

    def do_POST(self) -> None:
        self._serve_git()

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _serve_git(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        request_label = f"{self.command} {parsed.path}"
        if parsed.query:
            request_label += f"?{parsed.query}"
        self.server.request_log.append(request_label)
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        env = os.environ.copy()
        env.update(
            {
                "GIT_PROJECT_ROOT": str(self.server.repository_root),
                "GIT_HTTP_EXPORT_ALL": "1",
                "REQUEST_METHOD": self.command,
                "PATH_INFO": parsed.path,
                "QUERY_STRING": parsed.query,
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": str(content_length),
                "REMOTE_ADDR": self.client_address[0],
                "SERVER_PROTOCOL": self.request_version,
                "SERVER_NAME": "127.0.0.1",
                "SERVER_PORT": str(self.server.server_port),
            }
        )
        git_protocol = self.headers.get("Git-Protocol")
        if git_protocol:
            env["HTTP_GIT_PROTOCOL"] = git_protocol
        try:
            result = _run(["git", "http-backend"], env=env, input_bytes=body)
            header_bytes, response_body = _split_cgi_response(result.stdout)
            status = 200
            headers: list[tuple[str, str]] = []
            for raw_line in header_bytes.decode("latin-1").splitlines():
                if not raw_line:
                    continue
                name, separator, value = raw_line.partition(":")
                if not separator:
                    raise HermeticFixtureInvalid("git http-backend returned a malformed CGI header")
                if name.lower() == "status":
                    status = int(value.strip().split(" ", 1)[0])
                else:
                    headers.append((name.strip(), value.strip()))
            self.send_response(status)
            for name, value in headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except (HermeticFixtureInvalid, OSError, ValueError) as error:
            payload = f"smart Git fixture failure: {error}\n".encode("utf-8", errors="replace")
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


def _split_cgi_response(output: bytes) -> tuple[bytes, bytes]:
    for separator in (b"\r\n\r\n", b"\n\n"):
        if separator in output:
            headers, body = output.split(separator, 1)
            return headers, body
    raise HermeticFixtureInvalid("git http-backend returned no CGI header boundary")


class HermeticHttpsGitFixture:
    """Own one CA, HTTPS server, bare remote, immutable tag, and verified clone."""

    def __init__(self, source_root: Path):
        self._source_root = Path(source_root)
        self._fixture_root: Path | None = None
        self._server: _GitHttpServer | None = None
        self._thread: threading.Thread | None = None
        self._request_log: list[str] = []
        self._child_request_baseline: int | None = None
        self._closed = False
        self._source_commit = ""
        self._advertised_commit = ""
        self._candidate_digest = ""
        self._recloned_digest = ""
        self._tag = ""
        self._git_url = ""
        self._source = ""
        self._ca_file: Path | None = None

    def __enter__(self) -> "HermeticHttpsGitFixture":
        return self.start()

    def __exit__(self, exc_type: Any, exc_value: Any, _traceback: Any) -> bool:
        try:
            self.close()
        except HermeticFixtureInvalid as cleanup_error:
            if exc_value is None:
                raise
            if hasattr(exc_value, "add_note"):
                exc_value.add_note(str(cleanup_error))
        return False

    @property
    def fixture_root(self) -> Path:
        return self._require_started_root()

    @property
    def source_commit(self) -> str:
        self._require_started_root()
        return self._source_commit

    @property
    def advertised_commit(self) -> str:
        self._require_started_root()
        return self._advertised_commit

    @property
    def candidate_digest(self) -> str:
        self._require_started_root()
        return self._candidate_digest

    @property
    def recloned_digest(self) -> str:
        self._require_started_root()
        return self._recloned_digest

    @property
    def tag(self) -> str:
        self._require_started_root()
        return self._tag

    @property
    def git_url(self) -> str:
        self._require_started_root()
        return self._git_url

    @property
    def source(self) -> str:
        self._require_started_root()
        return self._source

    @property
    def ca_file(self) -> Path:
        self._require_started_root()
        if self._ca_file is None:
            raise HermeticFixtureInvalid("fixture CA is unavailable")
        return self._ca_file

    @property
    def request_count(self) -> int:
        return len(self._request_log)

    @property
    def request_log(self) -> tuple[str, ...]:
        return tuple(self._request_log)

    def start(self) -> "HermeticHttpsGitFixture":
        if self._fixture_root is not None:
            raise HermeticFixtureInvalid("fixture instance cannot be started twice")
        if shutil.which("git") is None or shutil.which("openssl") is None:
            raise HermeticFixtureInvalid("git and openssl are required for the HTTPS smart-Git fixture")
        self._candidate_digest = _tree_digest(self._source_root)
        self._fixture_root = Path(tempfile.mkdtemp(prefix="guru-https-git-"))
        try:
            self._prepare_repository()
            self._prepare_tls()
            self._start_server()
            self.verify_advertised_current_ref()
            self._verify_reclone()
            self._child_request_baseline = self.request_count
            return self
        except BaseException:
            try:
                self.close()
            except HermeticFixtureInvalid:
                pass
            raise

    def subprocess_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "GURU_HTTPS_SOURCE": self.source,
                "GURU_HTTPS_GIT_URL": self.git_url,
                "GURU_FIXTURE_TAG": self.tag,
                "GURU_FIXTURE_COMMIT": self.source_commit,
                "GURU_FIXTURE_CA": str(self.ca_file),
                "GURU_FIXTURE_CANDIDATE_DIGEST": self.candidate_digest,
                "GURU_FIXTURE_RECLONED_DIGEST": self.recloned_digest,
                "NODE_EXTRA_CA_CERTS": str(self.ca_file),
                "GIT_SSL_CAINFO": str(self.ca_file),
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        return env

    def verify_advertised_current_ref(
        self,
        *,
        tag: str | None = None,
        expected_commit: str | None = None,
    ) -> str:
        selected_tag = tag or self.tag
        selected_commit = expected_commit or self.source_commit
        result = _run(
            ["git", "ls-remote", "--refs", self.git_url, f"refs/tags/{selected_tag}"],
            env=self.subprocess_env(),
        )
        lines = [line for line in result.stdout.decode("utf-8").splitlines() if line.strip()]
        expected_line = f"{selected_commit}\trefs/tags/{selected_tag}"
        if lines != [expected_line]:
            raise HermeticFixtureInvalid(
                f"unique advertised current ref mismatch: expected {expected_line!r}, got {lines!r}"
            )
        self._advertised_commit = selected_commit
        return selected_commit

    def verify_child_git_activity(self) -> None:
        if self._child_request_baseline is None:
            raise HermeticFixtureInvalid("fixture preflight did not establish a request baseline")
        new_requests = self._request_log[self._child_request_baseline :]
        if not any("/info/refs?service=git-upload-pack" in item for item in new_requests):
            raise HermeticFixtureInvalid("child made no new HTTPS smart-Git upload-pack request")

    def close(self) -> None:
        if self._closed:
            return
        failures: list[str] = []
        if self._server is not None:
            try:
                self._server.shutdown()
                self._server.server_close()
            except OSError as error:
                failures.append(f"server shutdown: {error}")
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                failures.append("server thread did not stop")
        root = self._fixture_root
        if root is not None and root.exists():
            try:
                _remove_fixture_root(root)
            except OSError as error:
                failures.append(f"fixture root cleanup: {error}")
        self._closed = True
        if failures:
            raise HermeticFixtureInvalid("cleanup failed: " + "; ".join(failures))

    def _require_started_root(self) -> Path:
        if self._fixture_root is None or self._closed:
            raise HermeticFixtureInvalid("fixture is not active")
        return self._fixture_root

    def _prepare_repository(self) -> None:
        root = self._require_started_root()
        source_repo = root / "source"
        remote_parent = root / "repositories" / "org"
        bare_repo = remote_parent / "guru-fixture.git"
        source_repo.mkdir()
        shutil.copytree(self._source_root, source_repo, dirs_exist_ok=True)
        _run(["git", "init", "--quiet"], cwd=source_repo)
        _run(["git", "config", "user.name", "Guru Fixture"], cwd=source_repo)
        _run(["git", "config", "user.email", "fixture@example.invalid"], cwd=source_repo)
        _run(["git", "add", "--all"], cwd=source_repo)
        commit_env = os.environ.copy()
        commit_env.update(
            {
                "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
                "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
            }
        )
        _run(["git", "commit", "--quiet", "-m", "current Guru candidate"], cwd=source_repo, env=commit_env)
        self._source_commit = _run(["git", "rev-parse", "HEAD"], cwd=source_repo).stdout.decode().strip()
        nonce = secrets.token_hex(6)
        self._tag = f"guru-candidate-{self._source_commit[:12]}-{nonce}"
        _run(["git", "tag", self._tag], cwd=source_repo)
        remote_parent.mkdir(parents=True)
        _run(["git", "init", "--bare", "--quiet", str(bare_repo)])
        _run(["git", "remote", "add", "origin", str(bare_repo)], cwd=source_repo)
        _run(
            ["git", "push", "--quiet", "origin", "HEAD:refs/heads/candidate", f"refs/tags/{self._tag}"],
            cwd=source_repo,
        )
        _run(["git", "update-server-info"], cwd=bare_repo)

    def _prepare_tls(self) -> None:
        root = self._require_started_root()
        tls_root = root / "tls"
        tls_root.mkdir()
        ca_key = tls_root / "ca.key"
        ca_file = tls_root / "ca.pem"
        server_key = tls_root / "server.key"
        server_csr = tls_root / "server.csr"
        server_cert = tls_root / "server.pem"
        extension_file = tls_root / "server.ext"
        extension_file.write_text(
            "subjectAltName=IP:127.0.0.1\n"
            "extendedKeyUsage=serverAuth\n"
            "basicConstraints=CA:FALSE\n"
            "keyUsage=digitalSignature,keyEncipherment\n",
            encoding="ascii",
        )
        _run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-sha256",
                "-days",
                "2",
                "-subj",
                "/CN=Guru Fixture CA",
                "-keyout",
                str(ca_key),
                "-out",
                str(ca_file),
            ]
        )
        _run(
            [
                "openssl",
                "req",
                "-new",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-sha256",
                "-subj",
                "/CN=127.0.0.1",
                "-keyout",
                str(server_key),
                "-out",
                str(server_csr),
            ]
        )
        _run(
            [
                "openssl",
                "x509",
                "-req",
                "-in",
                str(server_csr),
                "-CA",
                str(ca_file),
                "-CAkey",
                str(ca_key),
                "-CAcreateserial",
                "-days",
                "2",
                "-sha256",
                "-extfile",
                str(extension_file),
                "-out",
                str(server_cert),
            ]
        )
        self._ca_file = ca_file
        self._server_key = server_key
        self._server_cert = server_cert

    def _start_server(self) -> None:
        root = self._require_started_root()
        repository_root = root / "repositories"
        server = _GitHttpServer(("127.0.0.1", 0), repository_root, self._request_log)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(self._server_cert), keyfile=str(self._server_key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever, name="guru-https-git", daemon=True)
        self._thread.start()
        port = server.server_port
        self._git_url = f"https://127.0.0.1:{port}/org/guru-fixture.git"
        self._source = f"https://127.0.0.1:{port}/org/guru-fixture#{self._tag}"
        validate_official_source(self._source)

    def _verify_reclone(self) -> None:
        root = self._require_started_root()
        clone = root / "verified-clone"
        _run(["git", "init", "--quiet", str(clone)])
        _run(["git", "remote", "add", "origin", self.git_url], cwd=clone)
        _run(
            ["git", "fetch", "--quiet", "--depth", "1", "origin", f"refs/tags/{self.tag}"],
            cwd=clone,
            env=self.subprocess_env(),
        )
        _run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], cwd=clone)
        cloned_commit = _run(["git", "rev-parse", "HEAD"], cwd=clone).stdout.decode().strip()
        if cloned_commit != self.source_commit:
            raise HermeticFixtureInvalid(
                f"recloned commit mismatch: expected {self.source_commit}, got {cloned_commit}"
            )
        self._recloned_digest = _tree_digest(clone, ignore_checkout_git=True)
        if self._recloned_digest != self.candidate_digest:
            raise HermeticFixtureInvalid(
                f"recloned candidate digest mismatch: expected {self.candidate_digest}, got {self._recloned_digest}"
            )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run one command inside a verified HTTPS Git fixture")
    run.add_argument("--source-root", required=True, type=Path)
    run.add_argument("--cwd", type=Path)
    run.add_argument("child", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    child = list(args.child)
    if child and child[0] == "--":
        child.pop(0)
    if not child:
        print("HermeticFixtureInvalid: run requires a child command", file=sys.stderr)
        return 2
    trap = _SignalTrap()
    previous_handlers = _install_signal_trap(trap)
    fixture = HermeticHttpsGitFixture(args.source_root)
    child_process: subprocess.Popen[Any] | None = None
    child_process_group: int | None = None
    primary_error: HermeticFixtureInvalid | None = None
    cleanup_error: HermeticFixtureInvalid | None = None
    exit_code = 0
    try:
        try:
            fixture.start()
            try:
                child_process = subprocess.Popen(
                    child,
                    cwd=args.cwd,
                    env=fixture.subprocess_env(),
                    start_new_session=True,
                )
            except OSError as error:
                raise HermeticFixtureInvalid(f"cannot start fixture child command: {error}") from error
            child_process_group = child_process.pid
            exit_code = child_process.wait()
            if exit_code == 0:
                fixture.verify_child_git_activity()
                print(
                    "HERMETIC_HTTPS_GIT_OK "
                    f"commit={fixture.source_commit} tag={fixture.tag} "
                    f"digest={fixture.candidate_digest} requests={fixture.request_count}"
                )
        except _ParentSignalReceived as error:
            trap.received = error.signum
            if child_process is not None and child_process_group is not None:
                failures = _terminate_child_process_group(
                    child_process,
                    child_process_group,
                    error.signum,
                )
                if failures:
                    error.add_note("; ".join(failures))
        except HermeticFixtureInvalid as error:
            primary_error = error
    finally:
        try:
            fixture.close()
        except _ParentSignalReceived as error:
            trap.received = trap.received or error.signum
            if child_process is not None and child_process_group is not None:
                failures = _terminate_child_process_group(
                    child_process,
                    child_process_group,
                    trap.received,
                )
                if failures:
                    error.add_note("; ".join(failures))
            try:
                fixture.close()
            except HermeticFixtureInvalid as retry_error:
                cleanup_error = retry_error
        except HermeticFixtureInvalid as error:
            cleanup_error = error
        _restore_signal_handlers(previous_handlers)

    if cleanup_error is not None:
        print(f"HermeticFixtureInvalid: {cleanup_error}", file=sys.stderr)
    if trap.received is not None:
        _redeliver_parent_signal(trap.received)
    if primary_error is not None:
        print(f"HermeticFixtureInvalid: {primary_error}", file=sys.stderr)
        return 3
    if cleanup_error is not None and exit_code == 0:
        return 3
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
