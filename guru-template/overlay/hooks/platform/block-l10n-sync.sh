#!/usr/bin/env bash
# PreToolUse(Bash)：拦截 l10n 同步脚本——双向写共享 Google Sheet，属人工受控步骤（golden-path §7）。
# 脚本名清单按目标项目 project-conventions SLOT-07 调整。
INPUT=$(cat)
# 只在「命令位/真正执行」判定，避免误伤 cat / git add / commit message / grep 等「提及脚本名」的无关调用
# （比照 block-unconfirmed-start.sh 的命令位扫描，而非对整段 INPUT 盲 grep）。
HIT=$(printf '%s' "$INPUT" | python3 -c '
import json, os, re, shlex, sys
try:
    cmd = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
except Exception:
    sys.exit(0)
BLOCKED_SCRIPTS = {"sync_translate.sh", "seek_l10_sync.sh"}
SEPS = {";", "&&", "||", "|", "&"}
INTERP = {"bash", "sh", "zsh", "source", "."}
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

for line in cmd.splitlines():
    try:
        lx = shlex.shlex(line, posix=True, punctuation_chars=True)
        lx.whitespace_split = True
        toks = list(lx)
    except ValueError:
        continue

    def at_cmd(i):
        j = i
        while j > 0 and ENV_ASSIGN.match(toks[j - 1]):
            j -= 1
        return j == 0 or toks[j - 1] in SEPS

    for i, t in enumerate(toks):
        base = os.path.basename(t)
        # 命令位直接执行（./sync_translate.sh、VAR=1 sync_translate.sh）或经解释器（bash sync_translate.sh）
        if base in BLOCKED_SCRIPTS and (at_cmd(i) or (i > 0 and os.path.basename(toks[i - 1]) in INTERP)):
            print("HIT"); sys.exit(0)
    # dart/flutter run ... l10n sync_translate 子命令形态
    if "l10n" in toks and "sync_translate" in toks:
        print("HIT"); sys.exit(0)
' 2>/dev/null)
[ -n "$HIT" ] || exit 0
echo "BLOCKED: l10n 同步脚本属人工受控步骤（SLOT-07），agent 禁止自动执行。需要同步请提示用户手动运行。" >&2
exit 2
