#!/usr/bin/env python3
"""after_create hook：新任务的 jsonl 自动注入 guru harness 基线条目（幂等）。

接入方式（目标项目 .trellis/config.yaml）：
  hooks:
    after_create:
      - "python3 .trellis/scripts/guru/guru_after_create.py"

环境：Trellis 在 hook 执行时提供 TASK_JSON_PATH 指向新任务的 task.json。
行为：
  1. 项目约定硬前置：.trellis/spec/conventions/project-conventions.md 缺失 → stderr 警告（不阻塞主流程，
     但 Gate 与各 skill 硬前置会拦）。
  2. 往 implement.jsonl / check.jsonl 追加基线条目（已存在的路径跳过，幂等）。
  3. task.json 默认写入 guru_chain=full（双轨制安全默认：完整五阶段链）。降为 light 必须
     经 client-small-iteration-dev 分流且获用户同意后显式改写。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
try:
    import guru_contract  # noqa: E402
except Exception:  # pragma: no cover - source-tree fallback, installed overlay has same-dir module
    guru_contract = None

BASELINE = [
    {"file": ".trellis/spec/conventions/project-conventions.md",
     "reason": "项目约定槽位取值与 SLOT-15 存量违例清单（所有阶段硬前置）"},
    {"file": ".trellis/spec/guides/golden-path.md",
     "reason": "通用方法 SSOT：分层依赖律、迷你路径、禁止清单"},
    {"file": ".trellis/spec/harness/index.md",
     "reason": "五阶段 SSOT 入口与 Gate 口径"},
]
CHECK_EXTRA = [
    {"file": ".trellis/spec/harness/implementation/implementation-trace-contract.md",
     "reason": "审核 trace 四节与证据口径"},
]

# 方法学目录（harness/conventions/guides）= 配置包维护，非项目 by-layer 实例。
# 其余 .trellis/spec/<layer>/ 顶层目录视作 by-layer 项目 spec（flutter/service/shared、
# backend、frontend、ios… 随平台不同），其 index.md 进基线导航。
METHODOLOGY_DIRS = {"harness", "conventions", "guides"}


def bylayer_index_entries(project_root: str) -> list:
    """发现已安装的 by-layer 项目 spec 层目录，把各层 index.md 作为基线导航条目。
    自适应平台（按 .trellis/spec/ 实际目录），缺失则返回空表。
    用 project_root（从 TASK_JSON_PATH 解出）定位 spec，不依赖进程 cwd；
    jsonl 条目仍写 project-relative 路径（注入侧按项目根解析）。"""
    spec = os.path.join(project_root, ".trellis", "spec")
    out = []
    if os.path.isdir(spec):
        for name in sorted(os.listdir(spec)):
            d = os.path.join(spec, name)
            if name in METHODOLOGY_DIRS or not os.path.isdir(d):
                continue
            if os.path.isfile(os.path.join(d, "index.md")):
                out.append({"file": f".trellis/spec/{name}/index.md",
                            "reason": f"项目 {name} 层实际模式导航（by-layer 项目 spec）"})
    return out


def append_unique(jsonl_path: str, entries: list) -> int:
    existing = set()
    if os.path.isfile(jsonl_path):
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    existing.add(json.loads(line).get("file", ""))
                except json.JSONDecodeError:
                    continue
    new_entries = [e for e in entries if e["file"] not in existing]
    if not new_entries:
        return 0
    # 既有文件末行无换行时先补一个，避免首条新条目粘到用户最后一行末尾（产生 {..}{..} 非法 jsonl 行）
    need_nl = False
    if os.path.isfile(jsonl_path) and os.path.getsize(jsonl_path) > 0:
        with open(jsonl_path, "rb") as r:
            r.seek(-1, os.SEEK_END)
            need_nl = r.read(1) != b"\n"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        if need_nl:
            f.write("\n")
        for e in new_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(new_entries)


def main() -> int:
    task_json = os.environ.get("TASK_JSON_PATH", "")
    if not task_json or not os.path.isfile(task_json):
        sys.stderr.write("[guru-after-create] 未获得 TASK_JSON_PATH，跳过\n")
        return 0
    task_dir = os.path.dirname(task_json)
    # 从 TASK_JSON_PATH 解项目根（<root>/.trellis/tasks/<task>/task.json），
    # 使后续 spec 扫描不依赖进程 cwd。
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(task_dir)))

    conv = os.path.join(project_root, ".trellis", "spec", "conventions",
                        "project-conventions.md")
    if not os.path.isfile(conv):
        sys.stderr.write(
            "[guru-after-create] 警告：项目约定文件缺失（%s）。"
            "writing/review 硬前置与 Gate 将拦截，请先按模板填写。\n" % conv)

    bylayer = bylayer_index_entries(project_root)
    a = append_unique(os.path.join(task_dir, "implement.jsonl"), BASELINE + bylayer)
    b = append_unique(os.path.join(task_dir, "check.jsonl"), BASELINE + CHECK_EXTRA + bylayer)

    # 判轨安全默认：guru_chain=full（轻量链须显式降级）
    chain_note = ""
    contract_note = ""
    try:
        with open(task_json, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("task.json 根节点必须是对象")
        if data.get("guru_chain") not in ("full", "light"):
            data["guru_chain"] = "full"
            # 原子写：先写临时文件再 replace，中断不会留下半截 task.json
            tmp_path = f"{task_json}.tmp.{os.getpid()}"
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                os.replace(tmp_path, task_json)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            chain_note = "；guru_chain 默认 full（降 light 需分流+用户同意）"
        if guru_contract is not None and not os.path.exists(os.path.join(task_dir, guru_contract.CONTRACT_FILE)):
            contract = guru_contract.default_contract(
                guru_contract.ROUTE_FULL_CHAIN,
                data.get("risk_level", "unknown"),
                created_by="guru_after_create",
            )
            contract["assessment"]["reasons"] = ["conservative recommendation: new Guru tasks start as full_chain until the user selects a route"]
            guru_contract.write_contract(task_dir, contract)
            contract_note = "；gate-contract 默认推荐 full_chain（用户可通过 intake/init-contract 选择 micro/lite/full）"
    except (ValueError, OSError) as e:
        # ValueError 覆盖 json.JSONDecodeError（其子类）与非对象根节点；保持 best-effort 不阻塞主流程
        sys.stderr.write(f"[guru-after-create] 警告：guru_chain 写入失败（{e}）\n")

    print(f"[guru-after-create] jsonl 基线注入完成（implement +{a} / check +{b}）{chain_note}{contract_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
