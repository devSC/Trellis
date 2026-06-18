#!/usr/bin/env bash
# PreToolUse(Bash)：拦截未过 Guru start Gate 的 task.py start（需求确认 + review evidence + detail 确认；
# 最终防线在 task.py 的 before_start 阻断钩子，本 hook 仅提早给出可读提示）。
INPUT=$(cat)
# 只检查 Bash 工具的 command 字段，避免误伤"提及该命令文本"的无关调用（如编辑文档/echo）
COMMAND=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
    print((d.get("tool_input") or {}).get("command") or "")
except Exception:
    pass' 2>/dev/null)
[ -n "$COMMAND" ] || exit 0
# shlex 按 token 识别 task.py start（引号包裹的字符串字面量不会误判），并顺带提取任务目录参数
HIT=$(COMMAND="$COMMAND" python3 - <<'PY'
import os, re, shlex

SEPS = {";", "&&", "||", "|", "&"}
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def scan_line(line):
    """只在"命令位"识别 task.py start（直接执行或经 python* 解释器）；
    作为其他命令参数出现（echo/printf/heredoc）不触发。返回任务目录参数或 '-'，未命中 None。"""
    try:
        # punctuation_chars=True：把 ; && || | & 切成独立 token，避免 "start;" 粘连漏判
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        toks = list(lexer)
    except ValueError:
        return None

    def at_cmd(i):
        # 跳过 VAR=value 前缀：`TRELLIS_X=1 python3 task.py start` 仍是命令位
        j = i
        while j > 0 and ENV_ASSIGN.match(toks[j - 1]):
            j -= 1
        return j == 0 or toks[j - 1] in SEPS

    for i, tok in enumerate(toks):
        # 精确 basename，不误伤 mytask.py 等
        if os.path.basename(tok) == "task.py" and i + 1 < len(toks) and toks[i + 1] == "start":
            # 解释器形态：跳过 -u/-X 等选项 token，按 basename 识别 /usr/bin/python3 等路径形式
            j = i - 1
            while j >= 0 and toks[j].startswith("-"):
                j -= 1
            via_python = (j >= 0
                          and os.path.basename(toks[j]).startswith("python")
                          and at_cmd(j))
            if at_cmd(i) or via_python:
                return toks[i + 2] if i + 2 < len(toks) and not toks[i + 2].startswith("-") else "-"
    return None


# 逐行解析：多行命令里换行是命令边界（shlex 把 \n 当空白，跨行 token 不构成命令位语义）
for _line in os.environ.get("COMMAND", "").splitlines():
    _hit = scan_line(_line)
    if _hit is not None:
        print(_hit)
        break
PY
)
[ -n "$HIT" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
TDIR=""
[ "$HIT" != "-" ] && TDIR="$HIT"
if ! python3 .trellis/scripts/guru/guru_gate.py check ${TDIR:+"$TDIR"} >&2; then
  echo "BLOCKED: Guru Gate 校验未通过，禁止 task.py start。请先运行 guru_gate.py status <task_dir> 查看下一步。" >&2
  exit 2
fi
exit 0
