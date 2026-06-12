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
    added = 0
    with open(jsonl_path, "a", encoding="utf-8") as f:
        for e in entries:
            if e["file"] in existing:
                continue
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
            added += 1
    return added


def main() -> int:
    task_json = os.environ.get("TASK_JSON_PATH", "")
    if not task_json or not os.path.isfile(task_json):
        sys.stderr.write("[guru-after-create] 未获得 TASK_JSON_PATH，跳过\n")
        return 0
    task_dir = os.path.dirname(task_json)

    conv = ".trellis/spec/conventions/project-conventions.md"
    if not os.path.isfile(conv):
        sys.stderr.write(
            "[guru-after-create] 警告：项目约定文件缺失（%s）。"
            "writing/review 硬前置与 Gate 将拦截，请先按模板填写。\n" % conv)

    a = append_unique(os.path.join(task_dir, "implement.jsonl"), BASELINE)
    b = append_unique(os.path.join(task_dir, "check.jsonl"), BASELINE + CHECK_EXTRA)

    # 判轨安全默认：guru_chain=full（轻量链须显式降级）
    chain_note = ""
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
    except (ValueError, OSError) as e:
        # ValueError 覆盖 json.JSONDecodeError（其子类）与非对象根节点；保持 best-effort 不阻塞主流程
        sys.stderr.write(f"[guru-after-create] 警告：guru_chain 写入失败（{e}）\n")

    print(f"[guru-after-create] jsonl 基线注入完成（implement +{a} / check +{b}）{chain_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
