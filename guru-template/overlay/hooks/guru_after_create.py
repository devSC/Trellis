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
    print(f"[guru-after-create] jsonl 基线注入完成（implement +{a} / check +{b}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
