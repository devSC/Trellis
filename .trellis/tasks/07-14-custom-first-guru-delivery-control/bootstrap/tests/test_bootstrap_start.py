from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE / "bootstrap_start.py"
REPO_ROOT = SOURCE.parents[4]
TASK = Path(".trellis/tasks/07-14-custom-first-guru-delivery-control")
REQ, OVERVIEW, DETAIL = "a" * 64, "b" * 64, "c" * 64


TASK_SCRIPT = r'''#!/usr/bin/env python3
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
root = Path.cwd(); task = root / sys.argv[2]; path = task / "task.json"
data = json.loads(path.read_text()); data["status"] = "in_progress"
path.write_text(json.dumps(data, indent=2))
key = os.environ.get("TRELLIS_CONTEXT_ID")
if key:
    session = root / ".trellis/.runtime/sessions" / f"{key}.json"
    session.parent.mkdir(parents=True, exist_ok=True)
    value = json.loads(session.read_text()) if session.exists() else {}
    value.update({"platform": "codex", "last_seen_at": datetime.now(timezone.utc).isoformat(), "current_task": sys.argv[2]})
    value.setdefault("current_run", None)
    session.write_text(json.dumps(value, indent=2))
hook = Path.cwd() / "guru-template/overlay/hooks/guru_after_start.py"
if os.environ.get("GURU_START_ATTEMPT_ID") and hook.is_file():
    env = os.environ.copy(); env["TASK_JSON_PATH"] = str(path)
    subprocess.run([sys.executable, str(hook)], env=env, check=True)
raise SystemExit(int(os.environ.get("FAKE_TASK_RC", "0")))
'''

GATE_SCRIPT = f'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

def collect_gate_artifacts(task_dir, gate, repo_root=None):
    task = Path(task_dir)
    return [
        {{"path": str(task / "prd.md"), "source": "task", "key": "task:prd.md"}},
        {{"path": str(task / "design.md"), "source": "task", "key": "task:design.md"}},
        {{"path": str(task / "implement.md"), "source": "task", "key": "task:implement.md"}},
    ]

def main():
    cmd = sys.argv[1]
    dirty = [".trellis/tasks/07-14-custom-first-guru-delivery-control/bootstrap/bootstrap_start.py", ".trellis/tasks/07-14-custom-first-guru-delivery-control/bootstrap/tests/test_bootstrap_start.py"] if os.environ.get("FAKE_BOOTSTRAP_DIRTY_SCOPE") else []
    if os.environ.get("FAKE_BLOCKED_REVIEW_DIRTY"):
        dirty.append(".trellis/tasks/07-14-custom-first-guru-delivery-control/review-records/implementation-reviews.jsonl")
    if cmd == "digest":
        print({{"requirements": "{REQ}", "overview": "{OVERVIEW}", "detail": "{DETAIL}"}}[sys.argv[2]])
    elif cmd == "slice-plan":
        reasons = ["PACKET_AMBIGUOUS_WITHOUT_SLICE"] + (["SCOPE_INVALID:delivery-control"] if dirty else [])
        blockers = ["SCOPE_INVALID"] if dirty else []
        print(json.dumps({{"route":"full_chain","risk":"high","blocking_reasons":reasons,"slices":[{{"slice_id":"delivery-control","depends_on":[],"parallel_blockers":blockers,"dirty_out_of_scope":dirty}}]}}))
    elif cmd == "detail":
        raise SystemExit(int(os.environ.get("FAKE_DETAIL_CHECK_RC", "0")))
    elif cmd == "check-start":
        raise SystemExit(int(os.environ.get("FAKE_START_CHECK_RC", "0")))
    elif cmd == "check-implementation":
        if os.environ.get("FAKE_CAS_CONFLICT"):
            path = Path.cwd() / sys.argv[2] / "task.json"
            data = json.loads(path.read_text()); data["external_writer"] = True
            path.write_text(json.dumps(data))
            raise SystemExit(2)
        raise SystemExit(int(os.environ.get("FAKE_POSTCHECK_RC", "0")))

if __name__ == "__main__":
    main()
'''

SUPERVISOR_SCRIPT = r'''#!/usr/bin/env python3
import os, sys
if os.environ.get("FAKE_SUPERVISOR_BOOTSTRAP_DIRTY"):
    sys.stderr.write("[guru-supervise] scope invalid,硬停(SCOPE_INVALID):out-of-scope dirty paths: ['.trellis/tasks/07-14-custom-first-guru-delivery-control/bootstrap-exception.jsonl', '.trellis/tasks/07-14-custom-first-guru-delivery-control/bootstrap/bootstrap_start.py', '.trellis/tasks/07-14-custom-first-guru-delivery-control/bootstrap/tests/test_bootstrap_start.py', '.trellis/tasks/07-14-custom-first-guru-delivery-control/review-records/implementation-reviews.jsonl']\n")
    raise SystemExit(2)
raise SystemExit(int(os.environ.get("FAKE_SUPERVISOR_RC", "0")))
'''


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Fixture:
    def __init__(self, current_run: object = "__absent_file__") -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self._write(self.root / "AGENTS.md", "# Fixture agent instructions\n")
        self.task = self.root / TASK
        (self.task / "bootstrap/tests").mkdir(parents=True)
        (self.task / "slice-packets").mkdir()
        (self.task / "risk-packets").mkdir()
        (self.task / "execution-envelopes").mkdir()
        (self.task / "review-records").mkdir()
        source = self.task / "bootstrap/bootstrap_start.py"
        shutil.copy2(SOURCE, source)
        self.source = source
        self.source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        scripts = self.root / ".trellis/scripts"
        (scripts / "guru").mkdir(parents=True)
        (scripts / "common").mkdir()
        self._write(scripts / "task.py", TASK_SCRIPT)
        self._write(scripts / "guru/guru_gate.py", GATE_SCRIPT)
        self._write(scripts / "guru/guru_supervise.py", SUPERVISOR_SCRIPT)
        for name in ("__init__.py", "active_task.py", "io.py", "log.py", "paths.py",
                     "task_utils.py", "config.py", "tasks.py", "types.py", "task_store.py",
                     "task_context.py", "git.py", "safe_commit.py"):
            self._write(scripts / "common" / name, "# fixed fake lifecycle dependency\n")
        shutil.copy2(REPO_ROOT / ".trellis/scripts/common/active_task.py", scripts / "common/active_task.py")
        self._write(self.root / ".trellis/config.yaml", "hooks: {{}}\n")
        hooks = self.root / "guru-template/overlay/hooks"
        verify = self.root / "guru-template/overlay/verify"
        (verify / "tests").mkdir(parents=True)
        hooks.mkdir(parents=True)
        shutil.copy2(REPO_ROOT / "guru-template/overlay/hooks/guru_task.py", hooks / "guru_task.py")
        shutil.copy2(REPO_ROOT / "guru-template/overlay/hooks/guru_after_start.py", hooks / "guru_after_start.py")
        shutil.copy2(REPO_ROOT / "guru-template/overlay/verify/guru_contract.py", verify / "guru_contract.py")
        shutil.copy2(REPO_ROOT / "guru-template/overlay/verify/guru_supervise.py", verify / "guru_supervise.py")
        review_record_source = verify / "guru_review_record.py"
        shutil.copy2(REPO_ROOT / "guru-template/overlay/verify/guru_review_record.py", review_record_source)
        review_record_source.write_text(
            review_record_source.read_text()
            + r'''

from pathlib import Path as _BootstrapTestPath
_bootstrap_test_target_snapshot_digest = target_snapshot_digest

def target_snapshot_digest(repo_root, target_paths, source="worktree"):
    value = _bootstrap_test_target_snapshot_digest(repo_root, target_paths, source)
    target = os.environ.get("FAKE_FINAL_REVIEW_DRIFT_PATH")
    marker = os.environ.get("FAKE_FINAL_REVIEW_DRIFT_MARKER")
    if target and marker:
        marker_path = _BootstrapTestPath(marker)
        if not marker_path.exists():
            marker_path.write_text("armed")
        elif marker_path.read_text() == "armed":
            path = _BootstrapTestPath(target)
            mode = os.environ.get("FAKE_FINAL_REVIEW_DRIFT_MODE", "append")
            if mode == "delete":
                path.unlink(missing_ok=True)
            elif mode == "replace":
                path.write_text("# final review replacement\n")
            else:
                path.write_text(path.read_text() + "# final review drift\n")
            marker_path.write_text("mutated")
    return value
''',
            encoding="utf-8",
        )
        self._write(verify / "guru_gate.py", GATE_SCRIPT)
        passing_test = (
            "import os, unittest\n"
            "from pathlib import Path\n"
            "class CapabilityTest(unittest.TestCase):\n"
            "    def test_live_capability(self):\n"
            "        target = os.environ.get('FAKE_BURN_DRIFT_PATH')\n"
            "        mode = os.environ.get('FAKE_BURN_DRIFT_MODE', 'append')\n"
            "        if target:\n"
            "            path = Path(target)\n"
            "            if mode == 'delete':\n"
            "                path.unlink(missing_ok=True)\n"
            "            elif mode == 'replace':\n"
            "                if not path.exists() or path.read_text() != '# burn replacement\\n':\n"
            "                    path.write_text('# burn replacement\\n')\n"
            "            elif not path.read_text().endswith('# burn drift\\n'):\n"
            "                path.write_text(path.read_text() + '# burn drift\\n')\n"
            "        self.assertTrue(True)\n"
            "if __name__ == '__main__': unittest.main()\n"
        )
        self._write(verify / "tests/test_delivery_policy.py", passing_test)
        self._write(verify / "tests/test_start_guard.py", passing_test)
        self._write(verify / "tests/run_tests.sh", "#!/usr/bin/env bash\nexit 0\n")
        os.chmod(verify / "tests/run_tests.sh", 0o755)
        self._write(self.task / "prd.md", "# Decisions\n\n- D1: fixture guarded start\n")
        self._write(self.task / "design.md", "# Fixture design\n")
        inventory = {
            "schema_version": 1,
            "task_id": "custom-first-guru-delivery-control",
            "scope": {
                "selected_slice_id": "delivery-control",
                "official_start_authority": "selected_slice_only",
                "later_slice_authority": "supervisor_fail_closed",
            },
            "slices": {"delivery-control": []},
        }
        self._write(
            self.task / "implement.md",
            "# Fixture implementation\n\n"
            "<!-- GURU:RISK_DECISION_INVENTORY:START -->\n"
            "```json\n"
            f"{json.dumps(inventory, indent=2, sort_keys=True)}\n"
            "```\n"
            "<!-- GURU:RISK_DECISION_INVENTORY:END -->\n",
        )
        review = lambda gate, i: {
            "run_id": f"{gate}-{i}", "reviewer": f"clean-context-{gate}-{i}",
            "artifact_digest": OVERVIEW if gate == "overview" else DETAIL,
            "result": "clean", "max_severity": "none", "evidence": "clean",
            **({"deletion_audit": "none; full deletion audit complete"} if gate == "detail" else {}),
        }
        task_json = {
            "id": "custom-first-guru-delivery-control", "status": "planning",
            "guru_gates": {
                "requirements": {"confirmed_by": "dev", "artifact_digest": REQ},
                "detail": {"confirmed_by": "dev", "confirmed_at": "2026-07-14T00:00:00Z", "artifact_digest": DETAIL},
                "review_runs": {
                    "overview": [review("overview", 1), review("overview", 2)],
                    "detail": [review("detail", 1), review("detail", 2)],
                },
            },
        }
        self._json(self.task / "task.json", task_json)
        self._json(self.task / "gate-contract.json", {"route": "full_chain", "risk": "high"})
        target_paths = [
            "guru-template/overlay/hooks/guru_task.py",
            "guru-template/overlay/hooks/guru_after_start.py",
            "guru-template/overlay/verify/tests/test_delivery_policy.py",
            "guru-template/overlay/verify/tests/test_start_guard.py",
            "guru-template/overlay/verify/tests/run_tests.sh",
        ]
        deterministic_checks = [
            "python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py'",
            "python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_start_guard.py'",
            "bash guru-template/overlay/verify/tests/run_tests.sh",
        ]
        packet = {
            "schema_version": 1,
            "slice_id": "delivery-control", "risk": "high", "depends_on": [],
            "target_paths": target_paths,
            "deterministic_checks": deterministic_checks,
            "semantic_review_provider": {"required": True, "provider": "opposite", "ocr": "optional"},
            "invariants": [
                {"invariant_id": "INV-START-001"},
                {"invariant_id": "INV-START-002"},
            ],
        }
        packet_path = self.task / "slice-packets/delivery-control.json"
        self._json(packet_path, packet)
        guru_task = load_module(hooks / "guru_task.py", f"fixture_guru_task_{id(self)}")
        gate_digest = guru_task._gate_digest(task_json, self.task)
        packet_digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        risk = {
            "schema_version": 1,
            "task_id": "custom-first-guru-delivery-control",
            "slice_id": "delivery-control",
            "route": "full_chain",
            "risk": "high",
            "slice_packet_digest": packet_digest,
            "artifact_digest": gate_digest,
            "detail_artifact_digest": DETAIL,
            "scope_fingerprint": "d" * 64,
            "policy_snapshot_digest": "c" * 64,
            "decision_universe_digest": guru_task._digest(tuple()),
            "decision_items": [],
            "decision_set_digest": guru_task._digest([]),
            "confirmation_required": False,
            "invariant_ids": ["INV-START-001", "INV-START-002"],
        }
        risk_path = self.task / "risk-packets/delivery-control.json"
        self._json(risk_path, risk)
        risk_digest = hashlib.sha256(risk_path.read_bytes()).hexdigest()
        envelope = {
            "schema_version": 1,
            "task_id": "custom-first-guru-delivery-control",
            "slice_id": "delivery-control",
            "execution_route": "full_chain",
            "slice_packet_digest": packet_digest,
            "risk_packet_digest": risk_digest,
            "scope_fingerprint": "d" * 64,
            "policy_snapshot_digest": "c" * 64,
        }
        self._json(self.task / "execution-envelopes/delivery-control.json", envelope)
        subprocess.run(["git", "add", "--", *target_paths], cwd=self.root, check=True)
        review_module = load_module(verify / "guru_review_record.py", f"fixture_review_{id(self)}")
        target_digest = review_module.target_snapshot_digest(str(self.root), target_paths, "index")
        self.assert_equal_target_digest = review_module.target_snapshot_digest(
            str(self.root), target_paths, "worktree"
        )
        if target_digest != self.assert_equal_target_digest:
            raise AssertionError("fixture index/worktree target digests diverged")
        self.target_paths = target_paths
        self.deterministic_results = [
            {"command": item, "exit_code": 0, "timed_out": False}
            for item in deterministic_checks
        ]
        self.target_digest = target_digest
        self.channel_root = self.home / ".trellis/channels"
        self.channel = "guru-07-14-custom-first-guru-delivery-control-check-fixture-clean-review"
        self.worker = "check-codex-fixture-clean-review"
        self.thread_id = "019f6107-b999-7e83-8fe5-022d1315bfb4"
        review = {
            "run_id": "fixture-clean-review",
            "slice_id": "delivery-control",
            "review_target": "slice:delivery-control",
            "review_result": "clean",
            "route_class": "none",
            "deterministic_checks": "passed",
            "dirty_scope": "isolated",
            "invariant_coverage": "all_passed",
            "supervisor_failure": "none",
            "required_satisfied": True,
            "repairable": False,
            "timestamp": None,
            "target_paths": target_paths,
            "implement_provider": "codex",
            "review_provider": "codex",
            "check_provider": "codex",
            "provider_override_source": "cli_same_provider",
            "same_provider_user_quote": "关闭调用claude",
            "high_risk_review_provider_policy": "codex",
            "review_target_kind": "slice",
            "message": "same-provider implementation-review authorized by user quote: 关闭调用claude",
            "channel": self.channel,
            "worker": self.worker,
            "reviewed_target_digest": target_digest,
            "deterministic_results": self.deterministic_results,
        }
        (self.task / "review-records/implementation-reviews.jsonl").write_text(
            json.dumps(review, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._write_control_plane_capture()
        self.session = self.root / ".trellis/.runtime/sessions/fixture-session.json"
        if current_run != "__absent_file__":
            value = {"current_task": "old-task"}
            if current_run != "__missing_key__":
                value["current_run"] = current_run
            self._json(self.session, value)

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    @staticmethod
    def _json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2))

    @staticmethod
    def _project_key(root: Path) -> str:
        slashed = str(root.resolve()).replace("/", "-").replace("\\", "-").replace("_", "-")
        return "".join(ch if ch.isascii() and (ch.isalnum() or ch in ".-") else "-" for ch in slashed)

    def _write_control_plane_capture(self) -> None:
        channel_dir = self.control_plane_dir()
        channel_dir.mkdir(parents=True)
        invocation_contract = {
            "schema_version": 1,
            "action": "implementation-review",
            "review_mode": "check_only",
            "run_id": "fixture-clean-review",
            "channel": self.channel,
            "worker": self.worker,
            "supervisor_source": "guru-template/overlay/verify/guru_supervise.py",
            "supervisor_source_sha256": hashlib.sha256(
                (self.root / "guru-template/overlay/verify/guru_supervise.py").read_bytes()
            ).hexdigest(),
            "slice_id": "delivery-control",
            "review_target": "slice:delivery-control",
            "digest_source": "index",
            "reviewed_target_digest": self.target_digest,
            "target_paths_sha256": hashlib.sha256(json.dumps(
                self.target_paths, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ).encode()).hexdigest(),
            "deterministic_status": "passed",
            "deterministic_results_sha256": hashlib.sha256(json.dumps(
                self.deterministic_results, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ).encode()).hexdigest(),
            "implement_provider": "codex",
            "review_provider": "codex",
            "check_provider": "codex",
            "provider_override_source": "cli_same_provider",
            "same_provider_user_quote": "关闭调用claude",
            "same_provider": True,
            "staged": True,
        }
        prompt = (
            f"Active task: {self.task.resolve()}\n"
            "Load the injected Guru cli skill(s): trellis-check.\n"
            "Review the exact implementation target under Guru quality rules without implementing or editing files.\n"
            "Do not implement or edit files; emit one verdict and stop.\n"
            "Implementation-review check-only required evidence path.\n"
            "review_invocation_contract="
            + json.dumps(invocation_contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
            "review_target=slice:delivery-control\n"
            "target_digest_source=index\n"
            f"reviewed_target_digest={self.target_digest}\n"
        )
        session_path = (
            self.home / ".codex/sessions/2026/07/15"
            / f"rollout-2026-07-15T00-00-00-{self.thread_id}.jsonl"
        )
        self.codex_session_path = session_path
        session_meta = {
            "timestamp": "2026-07-15T00:00:00Z",
            "type": "session_meta",
            "payload": {
                "session_id": self.thread_id,
                "id": self.thread_id,
                "cwd": str(self.root.resolve()),
                "originator": "trellis-channel",
                "cli_version": "test-cli",
                "source": "vscode",
                "model_provider": "fixture-provider",
            },
        }
        self._write(session_path, json.dumps(session_meta, sort_keys=True) + "\n")
        thread = {
            "id": self.thread_id,
            "sessionId": self.thread_id,
            "forkedFromId": None,
            "parentThreadId": None,
            "ephemeral": False,
            "modelProvider": "fixture-provider",
            "cwd": str(self.root.resolve()),
            "cliVersion": "test-cli",
            "source": "vscode",
            "path": str(session_path.resolve()),
        }
        log_rows = [
            "[supervisor] starting codex app-server",
            json.dumps({
                "id": 1,
                "result": {
                    "userAgent": "trellis-channel/test-cli (fixture; test) (trellis-channel; test)",
                    "codexHome": str((self.home / ".codex").resolve()),
                    "platformFamily": "unix",
                },
            }, sort_keys=True),
            json.dumps({
                "id": 2,
                "result": {
                    "thread": thread,
                    "model": "gpt-fixture",
                    "modelProvider": "fixture-provider",
                    "cwd": str(self.root.resolve()),
                    "runtimeWorkspaceRoots": [str(self.root.resolve())],
                    "instructionSources": [str((self.root / "AGENTS.md").resolve())],
                    "approvalPolicy": "never",
                },
            }, sort_keys=True),
            json.dumps({
                "method": "thread/started",
                "params": {"thread": thread},
            }, sort_keys=True),
            json.dumps({
                "method": "turn/completed",
                "params": {"threadId": self.thread_id, "turn": {"status": "completed"}},
            }, sort_keys=True),
        ]
        self._write(channel_dir / f"{self.worker}.log", "\n".join(log_rows) + "\n")
        self._write(channel_dir / f"{self.worker}.thread-id", self.thread_id)
        self._write(channel_dir / f"{self.worker}.session-id", self.thread_id)
        verdict = (
            "review_result=clean\n"
            "route_class=none\n"
            "review_target=slice:delivery-control\n"
            "review_provider=codex\n"
            "deterministic_checks=passed\n"
            "dirty_scope=isolated\n"
            "invariant_coverage=all_passed\n"
            "invariant_status.INV-START-001=pass\n"
            "invariant_evidence.INV-START-001=fixture guarded start evidence\n"
            "invariant_status.INV-START-002=pass\n"
            "invariant_evidence.INV-START-002=fixture lifecycle CAS evidence\n"
        )
        self.review_verdict = verdict
        events = [
            {"kind": "create", "by": "main", "cwd": str(self.root.resolve()),
             "task": str(self.task.resolve()), "scope": "project", "type": "chat",
            "description": "Guru implementation-review 07-14-custom-first-guru-delivery-control",
             "origin": "cli", "seq": 1},
            {"kind": "spawned", "by": "main", "as": self.worker,
             "provider": "codex", "agent": "check", "inboxPolicy": "explicitOnly",
             "pid": 12345,
             "files": [
                 str((TASK / "prd.md").as_posix()),
                 str((TASK / "design.md").as_posix()),
                 str((TASK / "implement.md").as_posix()),
                 str((TASK / "slice-packets/delivery-control.json").as_posix()),
             ],
             "manifests": [str((TASK / "check.jsonl").as_posix())],
             "seq": 2},
            {"kind": "message", "by": "main", "to": self.worker,
             "text": prompt, "origin": "cli", "seq": 3},
            {"kind": "turn_started", "by": self.worker, "worker": self.worker,
             "inputSeq": 3, "turnId": "msg:3", "seq": 4},
            {"kind": "message", "by": self.worker, "text": verdict, "seq": 5},
            {"kind": "done", "by": self.worker, "seq": 6},
            {"kind": "turn_finished", "by": self.worker, "worker": self.worker,
             "inputSeq": 3, "turnId": "msg:3", "outcome": "done", "seq": 7},
        ]
        self._write(
            channel_dir / "events.jsonl",
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in events),
        )

    def control_plane_dir(self) -> Path:
        return self.channel_root / self._project_key(self.root) / self.channel

    def cli(self, action: str, *, extra_env: dict[str, str] | None = None,
            task: str = str(TASK), slice_id: str = "delivery-control",
            source_sha: str | None = None, evidence: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in ("CODEX_THREAD_ID", "CODEX_SESSION_ID", "TRELLIS_CONTEXT_ID"):
            env.pop(key, None)
        env["TRELLIS_CONTEXT_ID"] = "fixture-session"
        env["HOME"] = str(self.home)
        env.pop("TRELLIS_CHANNEL_ROOT", None)
        env.update(extra_env or {})
        args = [sys.executable, str(self.source), action, task, "--slice", slice_id,
                "--source-sha256", source_sha or self.source_sha]
        if evidence is not None:
            args += ["--evidence", str(evidence)]
        return subprocess.run(args, cwd=self.root, env=env, text=True, capture_output=True)

    def events(self) -> list[dict[str, object]]:
        return [json.loads(line) for line in (self.task / "bootstrap-exception.jsonl").read_text().splitlines()]

    def burn_evidence(self) -> Path:
        path = self.task / "bootstrap/burn-evidence.json"
        value = {
            "schema_version": 3,
            "task_id": "custom-first-guru-delivery-control",
            "selected_slice_id": "delivery-control",
            "wrapper_entry_capability": "enforced_guarded_entry_only",
            "after_start_capability": "compensated",
            "direct_official_capability": "advisory",
            "decision_inventory_scope": "selected_slice_only",
            "later_slice_authority": "supervisor_fail_closed",
            "implementation_review_run_id": "fixture-clean-review",
            "bootstrap_review_authorization": {
                "kind": "codex_same_provider_user_directive_v1",
                "user_directive": "关闭调用claude",
                "provider": "codex",
                "review_mode": "check_only",
                "independence_claim": "none",
                "trusted_review_envelope_eligible": False,
            },
        }
        self._json(path, value)
        return path

    def review_record(self) -> tuple[Path, dict[str, object]]:
        path = self.task / "review-records/implementation-reviews.jsonl"
        value = json.loads(path.read_text())
        return path, value

    def write_review_record(self, path: Path, value: dict[str, object]) -> None:
        path.write_text(json.dumps(value, sort_keys=True) + "\n")

    def blocked_review_record(self) -> None:
        path = self.task / "review-records/implementation-reviews.jsonl"
        value = {
            "repairable": False,
            "review_result": "blocked",
            "review_target": "slice:delivery-control",
            "route_class": "none",
            "run_id": "fixture-check-1",
            "slice_id": "delivery-control",
            "supervisor_failure": "SCOPE_INVALID",
            "target_paths": [],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n")

    def close(self) -> None:
        self.tmp.cleanup()


class BootstrapStartTest(unittest.TestCase):
    def test_wrong_task_slice_and_hash_fail_closed(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("status", task=".trellis/tasks/wrong").returncode, 2)
            self.assertEqual(fx.cli("status", slice_id="wrong").returncode, 2)
            self.assertEqual(fx.cli("status", source_sha="0" * 64).returncode, 2)
        finally:
            fx.close()

    def test_exclusive_create_and_duplicate_run_are_rejected(self) -> None:
        fx = Fixture()
        try:
            log = fx.task / "bootstrap-exception.jsonl"
            log.write_bytes(b"")
            self.assertEqual(fx.cli("run").returncode, 2)
            self.assertEqual(log.read_bytes(), b"")
            log.unlink()
            self.assertEqual(fx.cli("run").returncode, 0)
            self.assertEqual(fx.cli("run").returncode, 2)
        finally:
            fx.close()

    def test_task_local_bootstrap_dirty_scope_is_one_shot_exception(self) -> None:
        fx = Fixture()
        try:
            result = fx.cli("run", extra_env={"FAKE_BOOTSTRAP_DIRTY_SCOPE": "1"})
            self.assertEqual(result.returncode, 0, result.stderr)
            prepared = fx.events()[0]["payload"]
            selected = [s for s in prepared["commands"]["slice_plan"]["stdout"].splitlines() if s]
            self.assertTrue(selected)
        finally:
            fx.close()

    def test_postcheck_accepts_exact_bootstrap_audit_dirty_scope(self) -> None:
        fx = Fixture()
        try:
            fx.blocked_review_record()
            result = fx.cli("run", extra_env={"FAKE_SUPERVISOR_BOOTSTRAP_DIRTY": "1"})
            self.assertEqual(result.returncode, 0, result.stderr)
            consumed = fx.events()[-1]["payload"]
            self.assertEqual(consumed["outcome"], "verified")
            self.assertEqual(consumed["delivery_control_dry_run"]["returncode"], 2)
        finally:
            fx.close()

    def test_retry_after_clean_compensation_preserves_failed_chain(self) -> None:
        fx = Fixture(None)
        try:
            fx.blocked_review_record()
            self.assertEqual(fx.cli("run", extra_env={"FAKE_SUPERVISOR_RC": "2"}).returncode, 2)
            fx.source.write_text(fx.source.read_text() + "\n# retry fix\n")
            fx.source_sha = hashlib.sha256(fx.source.read_bytes()).hexdigest()
            result = fx.cli("run", extra_env={"FAKE_SUPERVISOR_BOOTSTRAP_DIRTY": "1", "FAKE_BLOCKED_REVIEW_DIRTY": "1"})
            self.assertEqual(result.returncode, 0, result.stderr)
            events = fx.events()
            self.assertEqual([event["event"] for event in events], ["prepared", "consumed", "retry_prepared", "retry_consumed"])
            self.assertEqual(events[1]["payload"]["outcome"], "failed_compensated")
            self.assertEqual(events[3]["payload"]["outcome"], "verified")
        finally:
            fx.close()

    def test_torn_and_corrupt_middle_chain_are_rejected(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            self.assertEqual(fx.cli("burn", evidence=fx.burn_evidence()).returncode, 0)
            log = fx.task / "bootstrap-exception.jsonl"
            original = log.read_bytes()
            log.write_bytes(original[:-1])
            self.assertEqual(fx.cli("status").returncode, 2)
            lines = original.splitlines()
            middle = json.loads(lines[1]); middle["payload"]["outcome"] = "changed"
            middle["payload_sha256"] = hashlib.sha256(json.dumps(middle["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            lines[1] = json.dumps(middle, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            log.write_bytes(b"\n".join(lines) + b"\n")
            self.assertEqual(fx.cli("status").returncode, 2)
        finally:
            fx.close()

    def test_legacy_fake_sha_manifest_is_rejected(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            evidence = fx.task / "bootstrap/legacy-burn-evidence.json"
            fx._json(evidence, {
                "task_id": "custom-first-guru-delivery-control",
                "selected_slice_id": "delivery-control",
                "source_sha256": fx.source_sha,
                "wrapper_entry_capability": "enforced_guarded_entry_only",
                "after_start_capability": "compensated",
                "direct_official_capability": "advisory",
                "verified_delivery_control_target_digest": "1" * 64,
                "deterministic_check_summary_digest": "2" * 64,
                "implementation_review_record_digest": "3" * 64,
                "wrapper_capability_test_digest": "4" * 64,
            })
            result = fx.cli("burn", evidence=evidence)
            self.assertEqual(result.returncode, 2)
            self.assertIn("schema is not exact v3", result.stderr)
        finally:
            fx.close()

    def test_bootstrap_review_authorization_manifest_is_exact(self) -> None:
        cases = {
            "legacy_schema": lambda value: value.update({"schema_version": 2}),
            "wrong_kind": lambda value: value["bootstrap_review_authorization"].update({"kind": "trusted_review"}),
            "wrong_quote": lambda value: value["bootstrap_review_authorization"].update({"user_directive": "已确认"}),
            "wrong_provider": lambda value: value["bootstrap_review_authorization"].update({"provider": "claude"}),
            "false_independence": lambda value: value["bootstrap_review_authorization"].update({"independence_claim": "independent"}),
            "false_v2_eligibility": lambda value: value["bootstrap_review_authorization"].update({"trusted_review_envelope_eligible": True}),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                fx = Fixture()
                try:
                    self.assertEqual(fx.cli("run").returncode, 0)
                    evidence = fx.burn_evidence()
                    value = json.loads(evidence.read_text())
                    mutate(value)
                    fx._json(evidence, value)
                    result = fx.cli("burn", evidence=evidence)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("burn evidence", result.stderr)
                    self.assertEqual(fx.events()[-1]["event"], "consumed")
                finally:
                    fx.close()

    def test_same_provider_record_must_match_the_exact_user_directive(self) -> None:
        cases = {
            "opposite_provider": lambda record: record.update({"review_provider": "claude", "check_provider": "claude"}),
            "config_policy": lambda record: record.update({"provider_override_source": "config_policy"}),
            "wrong_quote": lambda record: record.update({"same_provider_user_quote": "已确认"}),
            "wrong_policy": lambda record: record.update({"high_risk_review_provider_policy": "opposite"}),
            "wrong_target_kind": lambda record: record.update({"review_target_kind": "staged"}),
            "worker_prose_only": lambda record: record.update({"message": "worker says user authorized"}),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                fx = Fixture()
                try:
                    self.assertEqual(fx.cli("run").returncode, 0)
                    path, record = fx.review_record()
                    mutate(record)
                    fx.write_review_record(path, record)
                    result = fx.cli("burn", evidence=fx.burn_evidence())
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("exact Codex bootstrap authorization", result.stderr)
                    self.assertEqual(fx.events()[-1]["event"], "consumed")
                finally:
                    fx.close()

    def test_codex_control_plane_capture_fails_closed(self) -> None:
        def update_events(fx: Fixture, mutate) -> None:
            path = fx.control_plane_dir() / "events.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows = mutate(rows)
            path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))

        def wrong_thread(fx: Fixture) -> None:
            (fx.control_plane_dir() / f"{fx.worker}.thread-id").write_text(
                "019f6107-b999-7e83-8fe5-022d1315bfb5"
            )

        def wrong_cwd(fx: Fixture) -> None:
            path = fx.control_plane_dir() / f"{fx.worker}.log"
            lines = path.read_text().splitlines()
            row = json.loads(lines[2])
            row["result"]["cwd"] = "/tmp/wrong"
            lines[2] = json.dumps(row, sort_keys=True)
            path.write_text("\n".join(lines) + "\n")

        def wrong_provider(fx: Fixture) -> None:
            update_events(fx, lambda rows: [
                ({**row, "provider": "claude"} if row.get("kind") == "spawned" else row)
                for row in rows
            ])

        def missing_done(fx: Fixture) -> None:
            update_events(fx, lambda rows: [row for row in rows if row.get("kind") != "done"])

        def file_change(fx: Fixture) -> None:
            def add(rows):
                rows.append({"kind": "progress", "by": fx.worker,
                             "detail": {"kind": "file_change"}, "seq": 8})
                return rows
            update_events(fx, add)

        def worker_findings(fx: Fixture) -> None:
            update_events(fx, lambda rows: [
                ({**row, "text": row["text"]
                    .replace("review_result=clean", "review_result=findings")
                    .replace("route_class=none", "route_class=IMPLEMENT_DEFECT")}
                 if row.get("kind") == "message" and row.get("by") == fx.worker else row)
                for row in rows
            ])

        def malformed_worker_verdict(fx: Fixture) -> None:
            update_events(fx, lambda rows: [
                ({**row, "text": "review verdict"}
                 if row.get("kind") == "message" and row.get("by") == fx.worker else row)
                for row in rows
            ])

        def worker_record_mismatch(fx: Fixture) -> None:
            update_events(fx, lambda rows: [
                ({**row, "text": row["text"].replace("dirty_scope=isolated", "dirty_scope=clean")}
                 if row.get("kind") == "message" and row.get("by") == fx.worker else row)
                for row in rows
            ])

        def wrong_prompt_digest(fx: Fixture) -> None:
            update_events(fx, lambda rows: [
                ({**row, "text": row["text"].replace(
                    f"reviewed_target_digest={fx.target_digest}",
                    f"reviewed_target_digest={'f' * 64}",
                )}
                 if row.get("kind") == "message" and row.get("by") == "main" else row)
                for row in rows
            ])

        def wrong_invocation_quote(fx: Fixture) -> None:
            update_events(fx, lambda rows: [
                ({**row, "text": row["text"].replace(
                    '"same_provider_user_quote":"关闭调用claude"',
                    '"same_provider_user_quote":"已确认"',
                )}
                 if row.get("kind") == "message" and row.get("by") == "main" else row)
                for row in rows
            ])

        def extra_worker(fx: Fixture) -> None:
            def add(rows):
                rows.append({
                    "kind": "spawned", "by": "main", "as": "check-codex-unrelated",
                    "provider": "codex", "agent": "check", "seq": 8,
                })
                return rows
            update_events(fx, add)

        def wrong_session_originator(fx: Fixture) -> None:
            row = json.loads(fx.codex_session_path.read_text())
            row["payload"]["originator"] = "fixture"
            fx.codex_session_path.write_text(json.dumps(row, sort_keys=True) + "\n")

        for name, mutate in {
            "thread_session_mismatch": wrong_thread,
            "wrong_cwd": wrong_cwd,
            "wrong_provider": wrong_provider,
            "missing_done": missing_done,
            "file_change": file_change,
            "worker_findings": worker_findings,
            "malformed_worker_verdict": malformed_worker_verdict,
            "worker_record_mismatch": worker_record_mismatch,
            "wrong_prompt_digest": wrong_prompt_digest,
            "wrong_invocation_quote": wrong_invocation_quote,
            "extra_worker": extra_worker,
            "wrong_session_originator": wrong_session_originator,
        }.items():
            with self.subTest(case=name):
                fx = Fixture()
                try:
                    self.assertEqual(fx.cli("run").returncode, 0)
                    mutate(fx)
                    result = fx.cli("burn", evidence=fx.burn_evidence())
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("bootstrap Codex", result.stderr)
                    self.assertEqual(fx.events()[-1]["event"], "consumed")
                finally:
                    fx.close()

    def test_redirected_channel_store_is_rejected(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            result = fx.cli(
                "burn",
                evidence=fx.burn_evidence(),
                extra_env={"TRELLIS_CHANNEL_ROOT": str(fx.channel_root)},
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("rejects redirected Trellis channel storage", result.stderr)
            self.assertEqual(fx.events()[-1]["event"], "consumed")
        finally:
            fx.close()

    def test_burn_requires_live_in_progress_task_state(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            task_json = fx.task / "task.json"
            data = json.loads(task_json.read_text())
            data["status"] = "completed"
            fx._json(task_json, data)
            result = fx.cli("burn", evidence=fx.burn_evidence())
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires task status in_progress", result.stderr)
            self.assertEqual(fx.events()[-1]["event"], "consumed")
        finally:
            fx.close()

    def test_control_plane_drift_during_burn_cannot_append_burned(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            events_path = fx.control_plane_dir() / "events.jsonl"
            result = fx.cli(
                "burn",
                evidence=fx.burn_evidence(),
                extra_env={"FAKE_BURN_DRIFT_PATH": str(events_path)},
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("bootstrap Codex channel events JSONL is invalid", result.stderr)
            self.assertEqual(fx.events()[-1]["event"], "consumed")
        finally:
            fx.close()

    def test_historical_archive_is_mandatory_and_cannot_be_an_entry_bypass(self) -> None:
        fx = Fixture()
        try:
            old_bytes, old_sha = fx.source.read_bytes(), fx.source_sha
            self.assertEqual(fx.cli("run").returncode, 0)
            evidence = fx.burn_evidence()
            fx.source.write_bytes(old_bytes + b"\n# hardened verifier\n")
            fx.source_sha = hashlib.sha256(fx.source.read_bytes()).hexdigest()

            for action in ("status", "burn"):
                with self.subTest(storage="missing", action=action):
                    result = fx.cli(action, evidence=evidence if action == "burn" else None)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("required file unavailable", result.stderr)

            archive = fx.task / "bootstrap/archive" / f"bootstrap_start.{old_sha}.py"
            archive.parent.mkdir()
            archive.write_bytes(old_bytes + b"\n# drift\n")
            for action in ("status", "burn"):
                with self.subTest(storage="drift", action=action):
                    result = fx.cli(action, evidence=evidence if action == "burn" else None)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("historical verified-consumed source bytes", result.stderr)

            archive.write_bytes(old_bytes)
            status = fx.cli("status")
            self.assertEqual(status.returncode, 0, status.stderr)
            payload = json.loads(status.stdout)["result"]
            self.assertEqual(payload["historical_verified_consumed_source"]["source_sha256"], old_sha)
            self.assertEqual(payload["current_verifier_source"]["sha256"], fx.source_sha)

            bypass = subprocess.run([
                sys.executable, str(archive), "status", str(TASK),
                "--slice", "delivery-control", "--source-sha256", old_sha,
            ], cwd=fx.root, text=True, capture_output=True)
            self.assertEqual(bypass.returncode, 2)
            self.assertIn("reviewed source SHA-256 mismatch", bypass.stderr)
        finally:
            fx.close()

    def test_rehashed_envelope_does_not_authorize_risk_packet_drift(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            risk_path = fx.task / "risk-packets/delivery-control.json"
            envelope_path = fx.task / "execution-envelopes/delivery-control.json"
            risk = json.loads(risk_path.read_text())
            risk["decision_universe_digest"] = "f" * 64
            fx._json(risk_path, risk)
            envelope = json.loads(envelope_path.read_text())
            envelope["risk_packet_digest"] = hashlib.sha256(risk_path.read_bytes()).hexdigest()
            fx._json(envelope_path, envelope)

            result = fx.cli("burn", evidence=fx.burn_evidence())
            self.assertEqual(result.returncode, 2)
            self.assertIn("live risk/envelope/inventory binding failed", result.stderr)
        finally:
            fx.close()

    def test_review_target_drift_is_rejected(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            target = fx.root / "guru-template/overlay/verify/tests/test_delivery_policy.py"
            target.write_text(target.read_text() + "\n# drift after review\n")
            result = fx.cli("burn", evidence=fx.burn_evidence())
            self.assertEqual(result.returncode, 2)
            self.assertIn("implementation review target digest is stale", result.stderr)
        finally:
            fx.close()

    def test_deterministic_review_results_and_required_review_class_fail_closed(self) -> None:
        cases = {
            "missing": lambda record: record["deterministic_results"].pop(),
            "order": lambda record: record["deterministic_results"].reverse(),
            "exit": lambda record: record["deterministic_results"][0].update({"exit_code": 1}),
            "timeout": lambda record: record["deterministic_results"][0].update({"timed_out": True}),
            "supplemental": lambda record: record.update({"supplemental": True}),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                fx = Fixture()
                try:
                    self.assertEqual(fx.cli("run").returncode, 0)
                    path, record = fx.review_record()
                    mutate(record)
                    fx.write_review_record(path, record)
                    result = fx.cli("burn", evidence=fx.burn_evidence())
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("implementation review", result.stderr)
                finally:
                    fx.close()

    def test_live_detail_and_implementation_checks_are_required_for_burn(self) -> None:
        cases = ({"FAKE_DETAIL_CHECK_RC": "2"}, {"FAKE_POSTCHECK_RC": "2"})
        for extra_env in cases:
            with self.subTest(extra_env=extra_env):
                fx = Fixture()
                try:
                    self.assertEqual(fx.cli("run").returncode, 0)
                    result = fx.cli("burn", evidence=fx.burn_evidence(), extra_env=extra_env)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("failed rc=2", result.stderr)
                finally:
                    fx.close()

    def test_probe_window_target_drift_cannot_append_burned(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            target = fx.root / "guru-template/overlay/verify/tests/test_delivery_policy.py"
            result = fx.cli(
                "burn",
                evidence=fx.burn_evidence(),
                extra_env={"FAKE_BURN_DRIFT_PATH": str(target)},
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("implementation review target digest is stale", result.stderr)
            self.assertEqual(fx.events()[-1]["event"], "consumed")
        finally:
            fx.close()

    def test_probe_window_historical_archive_drift_cannot_append_burned(self) -> None:
        for mode in ("append", "replace", "delete"):
            with self.subTest(mode=mode):
                fx = Fixture()
                try:
                    old_bytes, old_sha = fx.source.read_bytes(), fx.source_sha
                    self.assertEqual(fx.cli("run").returncode, 0)
                    evidence = fx.burn_evidence()
                    fx.source.write_bytes(old_bytes + b"\n# hardened verifier\n")
                    fx.source_sha = hashlib.sha256(fx.source.read_bytes()).hexdigest()
                    archive = fx.task / "bootstrap/archive" / f"bootstrap_start.{old_sha}.py"
                    archive.parent.mkdir()
                    archive.write_bytes(old_bytes)

                    result = fx.cli(
                        "burn",
                        evidence=evidence,
                        extra_env={
                            "FAKE_BURN_DRIFT_PATH": str(archive),
                            "FAKE_BURN_DRIFT_MODE": mode,
                        },
                    )
                    self.assertEqual(result.returncode, 2)
                    expected_error = (
                        "required file unavailable"
                        if mode == "delete"
                        else "historical verified-consumed source bytes"
                    )
                    self.assertIn(expected_error, result.stderr)
                    self.assertEqual(fx.events()[-1]["event"], "consumed")
                finally:
                    fx.close()

    def test_post_final_validator_archive_drift_cannot_append_burned(self) -> None:
        for mode in ("append", "replace", "delete"):
            with self.subTest(mode=mode):
                fx = Fixture()
                try:
                    old_bytes, old_sha = fx.source.read_bytes(), fx.source_sha
                    self.assertEqual(fx.cli("run").returncode, 0)
                    evidence = fx.burn_evidence()
                    fx.source.write_bytes(old_bytes + b"\n# hardened verifier\n")
                    fx.source_sha = hashlib.sha256(fx.source.read_bytes()).hexdigest()
                    archive = fx.task / "bootstrap/archive" / f"bootstrap_start.{old_sha}.py"
                    archive.parent.mkdir()
                    archive.write_bytes(old_bytes)
                    marker = fx.task / "bootstrap/final-review-drift.marker"

                    result = fx.cli(
                        "burn",
                        evidence=evidence,
                        extra_env={
                            "FAKE_FINAL_REVIEW_DRIFT_PATH": str(archive),
                            "FAKE_FINAL_REVIEW_DRIFT_MARKER": str(marker),
                            "FAKE_FINAL_REVIEW_DRIFT_MODE": mode,
                        },
                    )
                    self.assertEqual(result.returncode, 2)
                    expected_error = (
                        "required file unavailable"
                        if mode == "delete"
                        else "historical verified-consumed source bytes"
                    )
                    self.assertIn(expected_error, result.stderr)
                    self.assertEqual(fx.events()[-1]["event"], "consumed")
                finally:
                    fx.close()

    def test_official_failure_restores_exact_preimages(self) -> None:
        fx = Fixture({"run": "keep"})
        try:
            task_before, session_before = (fx.task / "task.json").read_bytes(), fx.session.read_bytes()
            result = fx.cli("run", extra_env={"FAKE_TASK_RC": "1"})
            self.assertEqual(result.returncode, 2)
            self.assertEqual((fx.task / "task.json").read_bytes(), task_before)
            self.assertEqual(fx.session.read_bytes(), session_before)
            self.assertEqual(fx.events()[-1]["payload"]["outcome"], "failed_compensated")
        finally:
            fx.close()

    def test_postcheck_failure_restores_exact_preimages(self) -> None:
        fx = Fixture(None)
        try:
            task_before, session_before = (fx.task / "task.json").read_bytes(), fx.session.read_bytes()
            self.assertEqual(fx.cli("run", extra_env={"FAKE_SUPERVISOR_RC": "2"}).returncode, 2)
            self.assertEqual((fx.task / "task.json").read_bytes(), task_before)
            self.assertEqual(fx.session.read_bytes(), session_before)
        finally:
            fx.close()

    def test_absent_missing_null_and_non_null_current_run(self) -> None:
        cases = [("__absent_file__", "session_file_absent", None),
                 ("__missing_key__", "absent", None), (None, "null", None),
                 ({"id": "existing"}, "value", {"id": "existing"})]
        for initial, state, expected in cases:
            with self.subTest(state=state):
                fx = Fixture(initial)
                try:
                    self.assertEqual(fx.cli("run").returncode, 0)
                    prepared = fx.events()[0]["payload"]
                    self.assertEqual(prepared["session_current_run_preimage"]["state"], state)
                    self.assertEqual(json.loads(fx.session.read_text())["current_run"], expected)
                finally:
                    fx.close()

    def test_cas_conflict_records_manual_recovery(self) -> None:
        fx = Fixture(None)
        try:
            self.assertEqual(fx.cli("run", extra_env={"FAKE_CAS_CONFLICT": "1"}).returncode, 2)
            consumed = fx.events()[-1]["payload"]
            self.assertEqual(consumed["outcome"], "manual_recovery_required")
            self.assertTrue(json.loads((fx.task / "task.json").read_text())["external_writer"])
        finally:
            fx.close()

    def test_duplicate_burn_and_changed_source_are_rejected(self) -> None:
        fx = Fixture()
        try:
            self.assertEqual(fx.cli("run").returncode, 0)
            evidence = fx.burn_evidence()
            self.assertEqual(fx.cli("burn", evidence=evidence).returncode, 0)
            self.assertEqual(fx.cli("burn", evidence=evidence).returncode, 2)
            fx.source.write_text(fx.source.read_text() + "\n")
            self.assertEqual(fx.cli("status").returncode, 2)
        finally:
            fx.close()


if __name__ == "__main__":
    unittest.main()
