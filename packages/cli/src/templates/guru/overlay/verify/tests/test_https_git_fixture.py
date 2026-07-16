import os
import signal
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tests"))
if FIXTURE_DIR not in sys.path:
    sys.path.insert(0, FIXTURE_DIR)

import https_git_fixture as fixture_module


class HermeticHttpsGitFixtureTests(unittest.TestCase):
    def make_source(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "guru-template"
        (root / "workflows").mkdir(parents=True)
        (root / "specs" / "guru-fixture").mkdir(parents=True)
        (root / "index.json").write_text('{"version":1,"templates":[]}\n', encoding="utf-8")
        (root / "workflows" / "fixture.md").write_text("# fixture\n", encoding="utf-8")
        (root / "specs" / "guru-fixture" / "README.md").write_text("fixture\n", encoding="utf-8")
        return root

    def test_https_smart_git_ref_and_reclone_bind_current_candidate(self):
        source = self.make_source()
        with fixture_module.HermeticHttpsGitFixture(source) as fixture:
            self.assertTrue(fixture.source.startswith("https://127.0.0.1:"))
            self.assertIn("/org/guru-fixture#", fixture.source)
            self.assertEqual(fixture.advertised_commit, fixture.source_commit)
            self.assertEqual(fixture.recloned_digest, fixture.candidate_digest)
            self.assertGreater(fixture.request_count, 0)
            paths = "\n".join(fixture.request_log)
            self.assertIn("/info/refs?service=git-upload-pack", paths)
            self.assertIn("/git-upload-pack", paths)
            self.assertTrue(fixture.ca_file.is_file())

    def test_official_source_rejects_local_file_and_unpinned_forms(self):
        invalid_sources = (
            "/tmp/repo",
            "file:///tmp/repo",
            "local:/tmp/repo",
            "https://127.0.0.1:1234/org/guru-fixture/guru-template",
            "https://127.0.0.1:1234/org/guru-fixture/guru-template#tag",
            "https://127.0.0.1:1234/org/guru-fixture.git#tag",
        )
        for source in invalid_sources:
            with self.subTest(source=source):
                with self.assertRaises(fixture_module.HermeticFixtureInvalid):
                    fixture_module.validate_official_source(source)

    def test_unadvertised_or_stale_ref_fails_closed(self):
        source = self.make_source()
        with fixture_module.HermeticHttpsGitFixture(source) as fixture:
            with self.assertRaises(fixture_module.HermeticFixtureInvalid):
                fixture.verify_advertised_current_ref(tag="missing-tag")
            with self.assertRaises(fixture_module.HermeticFixtureInvalid):
                fixture.verify_advertised_current_ref(expected_commit="0" * 40)

    def test_each_run_uses_a_new_remote_and_unique_ref(self):
        source = self.make_source()
        with fixture_module.HermeticHttpsGitFixture(source) as first:
            first_tag = first.tag
            first_root = first.fixture_root
        with fixture_module.HermeticHttpsGitFixture(source) as second:
            self.assertNotEqual(second.tag, first_tag)
            self.assertNotEqual(second.fixture_root, first_root)

    def test_child_activity_must_add_smart_git_requests(self):
        source = self.make_source()
        with fixture_module.HermeticHttpsGitFixture(source) as fixture:
            with self.assertRaises(fixture_module.HermeticFixtureInvalid):
                fixture.verify_child_git_activity()
            env = fixture.subprocess_env()
            subprocess.run(
                ["git", "ls-remote", fixture.git_url, f"refs/tags/{fixture.tag}"],
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            fixture.verify_child_git_activity()

    def test_cleanup_failure_is_not_reported_as_success(self):
        source = self.make_source()
        fixture = fixture_module.HermeticHttpsGitFixture(source)
        fixture.start()
        fixture_root = fixture.fixture_root
        with mock.patch.object(fixture_module, "_remove_fixture_root", side_effect=OSError("cleanup denied")):
            with self.assertRaisesRegex(fixture_module.HermeticFixtureInvalid, "cleanup"):
                fixture.close()
        shutil.rmtree(fixture_root, ignore_errors=True)

    def test_cli_run_exports_pinned_source_and_verifies_child_activity(self):
        source = self.make_source()
        script = Path(FIXTURE_DIR) / "https_git_fixture.py"
        child = (
            "import os,subprocess; "
            "assert os.environ['GURU_HTTPS_SOURCE'].startswith('https://127.0.0.1:'); "
            "subprocess.run(['git','ls-remote',os.environ['GURU_HTTPS_GIT_URL'],"
            "'refs/tags/'+os.environ['GURU_FIXTURE_TAG']],check=True)"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "run",
                "--source-root",
                str(source),
                "--",
                sys.executable,
                "-c",
                child,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("HERMETIC_HTTPS_GIT_OK", result.stdout)

    def assert_cli_signal_cleans_child_and_fixture(self, signum):
        source = self.make_source()
        script = Path(FIXTURE_DIR) / "https_git_fixture.py"
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        temporary_root = Path(temporary.name)
        ready_file = temporary_root / "child-ready"
        child = (
            "import os,socket,time; from pathlib import Path; "
            "server=socket.socket(); server.bind(('127.0.0.1',0)); server.listen(); "
            "Path(os.environ['GURU_CHILD_READY']).write_text("
            "f'{os.getpid()} {server.getsockname()[1]}',encoding='ascii'); "
            "time.sleep(3600)"
        )
        env = os.environ.copy()
        env.update({"TMPDIR": str(temporary_root), "GURU_CHILD_READY": str(ready_file)})
        process = subprocess.Popen(
            [
                sys.executable,
                str(script),
                "run",
                "--source-root",
                str(source),
                "--",
                sys.executable,
                "-c",
                child,
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        child_pid = None

        def stop_leaks():
            if process.poll() is None:
                process.kill()
                process.communicate()
            if child_pid is not None:
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        self.addCleanup(stop_leaks)
        deadline = time.monotonic() + 30
        while not ready_file.exists():
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.fail(f"fixture exited before child became ready: rc={process.returncode}\n{stdout}\n{stderr}")
            if time.monotonic() >= deadline:
                self.fail("fixture child did not become ready before deadline")
            time.sleep(0.02)
        child_pid_text, child_port_text = ready_file.read_text(encoding="ascii").split()
        child_pid = int(child_pid_text)
        child_port = int(child_port_text)
        process.send_signal(signum)
        stdout, stderr = process.communicate(timeout=15)
        self.assertEqual(process.returncode, -signum, f"stdout={stdout}\nstderr={stderr}")

        deadline = time.monotonic() + 5
        while list(temporary_root.glob("guru-https-git-*")):
            if time.monotonic() >= deadline:
                self.fail("fixture root survived parent signal cleanup")
            time.sleep(0.02)
        while True:
            with socket.socket() as client:
                client.settimeout(0.1)
                child_port_closed = client.connect_ex(("127.0.0.1", child_port)) != 0
            if child_port_closed:
                break
            if time.monotonic() >= deadline:
                self.fail(f"child server on port {child_port} survived parent signal cleanup")
            time.sleep(0.02)

    def test_cli_sigterm_cleans_child_group_and_fixture_root(self):
        self.assert_cli_signal_cleans_child_and_fixture(signal.SIGTERM)

    def test_cli_sigint_cleans_child_group_and_fixture_root(self):
        self.assert_cli_signal_cleans_child_and_fixture(signal.SIGINT)


if __name__ == "__main__":
    unittest.main()
