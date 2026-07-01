#!/usr/bin/env bash
# PreToolUse(Bash): block Guru implementation commits before task.py start and implementation review.
# This is an early, readable guard; guru_gate.py check-commit is the replayable source of truth.
INPUT=$(cat)

COMMAND=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
    print((d.get("tool_input") or {}).get("command") or d.get("command") or "")
except Exception:
    pass' 2>/dev/null)
[ -n "$COMMAND" ] || exit 0

HOOK_CWD=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
    print(d.get("cwd") or (d.get("tool_input") or {}).get("cwd") or "")
except Exception:
    pass' 2>/dev/null)

HIT=$(COMMAND="$COMMAND" HOOK_CWD="${HOOK_CWD:-${CLAUDE_PROJECT_DIR:-${CODEX_PROJECT_DIR:-.}}}" python3 - <<'PY'
import os
import re
import shlex
import subprocess

SEPS = {";", ";;", ";&", ";;&", "&&", "||", "|", "&", ")", ");", "}", "};"}
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
REDIR_OPS = {">", ">>", "<", "<<", "<<<", "<>", ">|", "&>", "&>>", ">&", "<&"}
GIT_VALUE_OPTIONS = {"-C", "--git-dir", "--work-tree", "--namespace"}
GIT_ROOT_OPTIONS = {"-C", "--git-dir", "--work-tree"}
GIT_ROOT_ENV_KEYS = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"}
SHELL_PREFIXES = {"builtin", "command", "exec", "sudo", "env", "time", "nice", "nohup"}
SHELL_EXECUTORS = {"bash", "sh", "zsh"}
ARGV_EXECUTORS = {"xargs", "parallel"}
SHELL_DYNAMIC_EXECUTORS = {"eval", "source", "."}
SHELL_KEYWORDS = {"if", "then", "else", "elif", "case", "in", "do", "while", "until", "for", "select", "!", "(", "{"}
ENV_VALUE_OPTIONS = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}
HOOK_CWD = os.environ.get("HOOK_CWD") or "."


def _normalize_command(text):
    return text.replace("\\\r\n", " ").replace("\\\n", " ")


def _tokens(line):
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def _segment_prefix(toks, i):
    start = i
    while start > 0 and toks[start - 1] not in SEPS:
        start -= 1
    return toks[start:i]


def _prefix_has_cwd_change(prefix):
    for j, tok in enumerate(prefix):
        if tok == "env":
            k = j + 1
            while k < len(prefix):
                opt = prefix[k]
                if opt in {"-C", "--chdir"} or opt.startswith("--chdir="):
                    return True
                if opt in SEPS:
                    break
                k += 1
    return False


def _prefix_has_git_root_env(prefix):
    for tok in prefix:
        match = ENV_ASSIGN.match(tok)
        if not match:
            continue
        key = tok.split("=", 1)[0]
        if key in GIT_ROOT_ENV_KEYS:
            return True
    return False


def _drop_leading_redirs(prefix):
    changed = False
    while prefix:
        if len(prefix) >= 3 and re.match(r"^\d+$", prefix[0]) and prefix[1] in REDIR_OPS:
            del prefix[:3]
            changed = True
            continue
        if prefix[0] in REDIR_OPS:
            if len(prefix) >= 2:
                del prefix[:2]
            else:
                del prefix[:1]
            changed = True
            continue
        break
    return changed


def _at_cmd(toks, i):
    prefix = _segment_prefix(toks, i)
    if len(prefix) >= 3 and prefix[-1] == "{" and prefix[-2] == "()" and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", prefix[-3]):
        prefix = prefix[:-3]
    if len(prefix) >= 3 and prefix[0] == "function" and prefix[-1] == "{":
        prefix = []
    while prefix and prefix[0] in SHELL_KEYWORDS:
        prefix.pop(0)
    _drop_leading_redirs(prefix)
    while prefix and ENV_ASSIGN.match(prefix[0]):
        prefix.pop(0)
    _drop_leading_redirs(prefix)
    while prefix and os.path.basename(prefix[0]) in SHELL_PREFIXES:
        wrapper = os.path.basename(prefix.pop(0))
        if wrapper == "builtin":
            pass
        elif wrapper == "command":
            if prefix and prefix[0] in {"-v", "-V"}:
                return False
            if prefix and prefix[0] == "-p":
                prefix.pop(0)
        elif wrapper == "exec":
            while prefix and prefix[0].startswith("-"):
                opt = prefix.pop(0)
                if opt == "-a" and prefix:
                    prefix.pop(0)
        elif wrapper == "sudo":
            while prefix and prefix[0].startswith("-"):
                opt = prefix.pop(0)
                if (
                    opt in {"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "--close-from"}
                    and prefix
                ):
                    prefix.pop(0)
        elif wrapper == "env":
            while prefix and prefix[0].startswith("-"):
                opt = prefix.pop(0)
                if opt in ENV_VALUE_OPTIONS and prefix:
                    prefix.pop(0)
            while prefix and ENV_ASSIGN.match(prefix[0]):
                prefix.pop(0)
        elif wrapper == "nice":
            while prefix and prefix[0].startswith("-"):
                opt = prefix.pop(0)
                if opt in {"-n", "--adjustment"} and prefix:
                    prefix.pop(0)
        elif wrapper == "time":
            while prefix and prefix[0].startswith("-"):
                prefix.pop(0)
        while prefix and ENV_ASSIGN.match(prefix[0]):
            prefix.pop(0)
        _drop_leading_redirs(prefix)
    return not prefix


def _resolve_cwd(base, target):
    if not target or target in SEPS or target == "-":
        return None
    if target == "--":
        return os.path.abspath(base or HOOK_CWD)
    if target.startswith("-"):
        return None
    expanded = os.path.expanduser(target)
    if os.path.isabs(expanded):
        return os.path.abspath(expanded)
    return os.path.abspath(os.path.join(base or HOOK_CWD, expanded))


def _cd_target(toks, i, current_cwd):
    j = i + 1
    while j < len(toks) and toks[j] not in SEPS:
        tok = toks[j]
        if tok == "--":
            j += 1
            continue
        if tok.startswith("-"):
            return None
        return _resolve_cwd(current_cwd, tok)
    return os.path.expanduser("~")


def _prefix_cwd(prefix, current_cwd):
    cwd = current_cwd
    for j, tok in enumerate(prefix):
        if tok != "env":
            continue
        k = j + 1
        while k < len(prefix):
            opt = prefix[k]
            if opt in SEPS:
                break
            if opt in {"-C", "--chdir"}:
                if k + 1 < len(prefix):
                    next_cwd = _resolve_cwd(cwd, prefix[k + 1])
                    cwd = next_cwd or cwd
                k += 2
                continue
            if opt.startswith("--chdir="):
                next_cwd = _resolve_cwd(cwd, opt.split("=", 1)[1])
                cwd = next_cwd or cwd
            k += 1
    return cwd


def _git_env_aliases(prefix):
    indexed = {}
    for tok in prefix:
        match = ENV_ASSIGN.match(tok)
        if not match:
            continue
        key, value = tok.split("=", 1)
        key_match = re.match(r"^GIT_CONFIG_KEY_(\d+)$", key)
        value_match = re.match(r"^GIT_CONFIG_VALUE_(\d+)$", key)
        if key_match:
            indexed.setdefault(key_match.group(1), {})["key"] = value
        elif value_match:
            indexed.setdefault(value_match.group(1), {})["value"] = value
    aliases = {}
    for pair in indexed.values():
        key = pair.get("key", "")
        value = pair.get("value", "")
        match = re.match(r"^alias\.([^=]+)$", key)
        if match:
            aliases[match.group(1)] = value
    return aliases


def _alias_value_is_commit(alias_value, remaining, git_cwd, aliases, commit_vars):
    if not isinstance(alias_value, str) or not alias_value.strip():
        return False
    alias_value = alias_value.strip()
    if not alias_value.startswith("!"):
        return bool(re.search(r"\bcommit\b", alias_value))
    shell_body = alias_value[1:].strip()
    if not shell_body:
        return True
    if re.search(r"\bcommit\b", shell_body):
        return True
    try:
        body_toks = _tokens(shell_body)
    except ValueError:
        return True
    if not body_toks:
        return True
    if any(tok in SEPS or tok in SHELL_DYNAMIC_EXECUTORS for tok in body_toks):
        return True
    combined = body_toks + list(remaining)
    for idx, tok in enumerate(body_toks):
        if os.path.basename(tok) != "git" or not _at_cmd(body_toks, idx):
            continue
        subcommand, _root_option = _git_subcommand(
            combined,
            idx,
            git_cwd,
            aliases,
            commit_vars,
        )
        return subcommand == "commit"
    # Shell aliases can execute arbitrary code; only simple git wrappers above
    # are proven safe enough to ignore.
    return True


def _git_subcommand(toks, i, cwd, env_aliases=None, commit_vars=None):
    j = i + 1
    root_option = False
    aliases = dict(env_aliases or {})
    commit_vars = set(commit_vars or [])
    git_cwd = cwd or HOOK_CWD
    while j < len(toks):
        tok = toks[j]
        if tok in SEPS:
            return None, root_option
        if tok in GIT_ROOT_OPTIONS or tok.startswith("--git-dir=") or tok.startswith("--work-tree="):
            root_option = True
        if tok == "-C":
            if j + 1 < len(toks):
                next_cwd = _resolve_cwd(git_cwd, toks[j + 1])
                git_cwd = next_cwd or git_cwd
            j += 2
            continue
        if tok == "-c":
            if j + 1 < len(toks):
                match = re.match(r"^alias\.([^=]+)=(.*)$", toks[j + 1])
                if match:
                    aliases[match.group(1)] = match.group(2)
            j += 2
            continue
        if tok.startswith("-c") and len(tok) > 2:
            match = re.match(r"^alias\.([^=]+)=(.*)$", tok[2:])
            if match:
                aliases[match.group(1)] = match.group(2)
            j += 1
            continue
        if tok in GIT_VALUE_OPTIONS:
            j += 2
            continue
        if tok.startswith("--git-dir=") or tok.startswith("--work-tree=") or tok.startswith("--namespace="):
            j += 1
            continue
        if tok.startswith("-"):
            j += 1
            continue
        if any(_refs_var(tok, name) for name in commit_vars):
            return "commit", root_option
        if tok in aliases:
            alias_scope = dict(aliases)
            alias_value = alias_scope.pop(tok)
            if _alias_value_is_commit(alias_value, toks[j + 1:], git_cwd, alias_scope, commit_vars):
                return "commit", root_option
            return tok, root_option
        configured_alias = _configured_git_alias(tok, git_cwd)
        if configured_alias and _alias_value_is_commit(configured_alias, toks[j + 1:], git_cwd, aliases, commit_vars):
            return "commit", root_option
        return tok, root_option
    return None, root_option


def _configured_git_alias(name, cwd=None):
    if not isinstance(name, str) or not re.match(r"^[A-Za-z0-9_.-]+$", name):
        return ""
    run_cwd = cwd if cwd and os.path.isdir(cwd) else None
    try:
        result = subprocess.run(
            ["git", "config", "--get", f"alias.{name}"],
            cwd=run_cwd,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _shell_c_arg(toks, i):
    j = i + 1
    while j < len(toks):
        tok = toks[j]
        if tok in SEPS:
            return None
        if tok == "-c" or (tok.startswith("-") and not tok.startswith("--") and "c" in tok[1:]):
            return toks[j + 1] if j + 1 < len(toks) else None
        j += 1
    return None


def _join_shell_words(words):
    return " ".join(shlex.quote(word) for word in words if word)


def _env_nested_command(split_value, rest):
    try:
        words = shlex.split(split_value)
    except ValueError:
        words = [split_value]
    words.extend(rest)
    return _join_shell_words(words)


def _env_split_args(toks, i):
    args = []
    j = i + 1
    while j < len(toks):
        tok = toks[j]
        if tok in SEPS:
            return args
        if tok == "--":
            return args
        if tok in {"-S", "--split-string"}:
            if j + 1 < len(toks) and toks[j + 1] not in SEPS:
                rest = []
                k = j + 2
                while k < len(toks) and toks[k] not in SEPS:
                    rest.append(toks[k])
                    k += 1
                args.append(_env_nested_command(toks[j + 1], rest))
            return args
        if tok.startswith("--split-string="):
            split_value = tok.split("=", 1)[1]
            rest = []
            k = j + 1
            while k < len(toks) and toks[k] not in SEPS:
                rest.append(toks[k])
                k += 1
            args.append(_env_nested_command(split_value, rest))
            return args
        if tok.startswith("-S") and len(tok) > 2:
            split_value = tok[2:]
            rest = []
            k = j + 1
            while k < len(toks) and toks[k] not in SEPS:
                rest.append(toks[k])
                k += 1
            args.append(_env_nested_command(split_value, rest))
            return args
        if tok in {"-u", "--unset", "-C", "--chdir"}:
            j += 2
            continue
        if tok.startswith("--unset=") or tok.startswith("--chdir="):
            j += 1
            continue
        if tok.startswith("-"):
            j += 1
            continue
        if ENV_ASSIGN.match(tok):
            j += 1
            continue
        return args
    return args


def _has_unquoted_substitution_commit(line):
    in_single = False
    in_double = False
    escaped = False
    for i, ch in enumerate(line):
        if escaped:
            escaped = False
            continue
        if ch == "\\" and not in_single:
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single:
            continue
        if ch == chr(96):
            end = line.find(chr(96), i + 1)
            payload = line[i + 1 :] if end == -1 else line[i + 1 : end]
            if re.search(r"\bgit\b", payload) and re.search(r"\bcommit\b", payload):
                return True
            continue
        for marker in ("$" + "(", "<" + "(", ">" + "("):
            if line.startswith(marker, i):
                payload = _balanced_substitution_payload(line, i + len(marker))
                if re.search(r"\bgit\b", payload) and re.search(r"\bcommit\b", payload):
                    return True
    return False


def _balanced_substitution_payload(line, start):
    depth = 1
    escaped = False
    in_single = False
    in_double = False
    j = start
    while j < len(line):
        ch = line[j]
        if escaped:
            escaped = False
            j += 1
            continue
        if ch == "\\" and not in_single:
            escaped = True
            j += 1
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            j += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            j += 1
            continue
        if not in_single and ch == "(":
            depth += 1
        elif not in_single and ch == ")":
            depth -= 1
            if depth == 0:
                return line[start:j]
        j += 1
    return line[start:]


def _dynamic_shell_parts(toks, i):
    parts = []
    j = i + 1
    while j < len(toks) and toks[j] not in SEPS:
        parts.append(toks[j])
        j += 1
    return parts


def _has_dynamic_shell_meta(value):
    return any(ch in value for ch in ("$", chr(96), "(", ")", "<", ">", "{", "}"))


def _literal_assignments_before(toks, end):
    assignments = {}
    for tok in toks[:end]:
        if tok in SEPS:
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", tok)
        if match and not _has_dynamic_shell_meta(match.group(2)):
            assignments[match.group(1)] = match.group(2)
    return assignments


def _resolve_literal_source_target(target, assignments):
    match = re.match(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$", target)
    if match and assignments:
        return assignments.get(match.group(1), target)
    return target


def _source_target_state(parts, cwd=None, assignments=None):
    if not parts:
        return "unknown"
    target = _resolve_literal_source_target(parts[0], assignments or {})
    if target == "/dev/null":
        return "safe"
    if target.startswith("-") or target == "-" or _has_dynamic_shell_meta(target):
        return "unknown"
    base = cwd or HOOK_CWD
    path = target if os.path.isabs(target) else os.path.join(base, target)
    try:
        if not os.path.isfile(path):
            return "unknown"
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return "unknown"
    return "commit" if re.search(r"\bgit\b", text) and re.search(r"\bcommit\b", text) else "safe"


def _shell_receives_stdin(toks, i):
    if i > 0 and toks[i - 1] == "|":
        return True
    j = i + 1
    while j < len(toks) and toks[j] not in SEPS:
        if toks[j] in {"<", "<<", "<<<"}:
            return True
        j += 1
    return False


def _heredoc_delimiters(line):
    try:
        toks = _tokens(line)
    except ValueError:
        return []
    delimiters = []
    for i, tok in enumerate(toks):
        if tok != "<<" or i + 1 >= len(toks):
            continue
        delim = toks[i + 1]
        allow_tabs = False
        if delim == "-" and i + 2 < len(toks):
            allow_tabs = True
            delim = toks[i + 2]
        elif delim.startswith("-"):
            allow_tabs = True
            delim = delim[1:]
        if not delim or _has_dynamic_shell_meta(delim):
            continue
        delimiters.append((delim, allow_tabs))
    return delimiters


def _strip_heredoc_bodies(command):
    output = []
    pending = []
    active = None
    for line in command.splitlines():
        if active:
            delim, allow_tabs = active
            candidate = line.lstrip("\t") if allow_tabs else line
            if candidate.strip() == delim:
                active = pending.pop(0) if pending else None
            continue
        output.append(line)
        pending.extend(_heredoc_delimiters(line))
        if pending:
            active = pending.pop(0)
    return "\n".join(output)


def _heredoc_bodies(command):
    bodies = []
    pending = []
    active = None
    current = []
    for line in command.splitlines():
        if active:
            delim, allow_tabs = active
            candidate = line.lstrip("\t") if allow_tabs else line
            if candidate.strip() == delim:
                bodies.append("\n".join(current))
                current = []
                active = pending.pop(0) if pending else None
            else:
                current.append(line)
            continue
        pending.extend(_heredoc_delimiters(line))
        if pending:
            active = pending.pop(0)
            current = []
    if active and current:
        bodies.append("\n".join(current))
    return bodies


def _has_executable_heredoc_commit(command):
    bodies = _heredoc_bodies(command)
    if not any(re.search(r"\bgit\b", body) and re.search(r"\bcommit\b", body) for body in bodies):
        return False
    stripped = _strip_heredoc_bodies(command)
    try:
        toks = _tokens(_normalize_command(stripped))
    except ValueError:
        return bool(re.search(r"\b(?:eval|source|bash|sh|zsh)\b", stripped))
    for i, tok in enumerate(toks):
        base = os.path.basename(tok)
        if base in SHELL_DYNAMIC_EXECUTORS and _at_cmd(toks, i):
            return True
        if base in SHELL_EXECUTORS and _at_cmd(toks, i):
            return True
    if re.search(r"\bchmod\b.*\+x|(?:^|[;&|])\s*(?:\./|/|~)", stripped):
        return True
    return False


def _has_multiline_indirect_eval_commit(command):
    if "\n" not in command:
        return False
    assigned = set()
    for line in command.splitlines():
        try:
            toks = _tokens(_normalize_command(line))
        except ValueError:
            if re.search(r"\bgit\b", line) and re.search(r"\bcommit\b", line) and assigned:
                return True
            continue
        for tok in toks:
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", tok)
            if match and re.search(r"\bgit\b", match.group(2)) and re.search(r"\bcommit\b", match.group(2)):
                assigned.add(match.group(1))
        if "eval" in toks:
            payload = " ".join(toks)
            if re.search(r"\bgit\b", payload) and re.search(r"\bcommit\b", payload):
                return True
            for name in assigned:
                if re.search(r"(\$" + re.escape(name) + r"\b|\$\{" + re.escape(name) + r"\})", payload):
                    return True
    return False


def _commit_assignment_vars(toks):
    assigned = set()
    for tok in toks:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", tok)
        if match and re.search(r"\bgit\b", match.group(2)) and re.search(r"\bcommit\b", match.group(2)):
            assigned.add(match.group(1))
    return assigned


def _literal_assignment_vars(toks, value):
    assigned = set()
    for tok in toks:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", tok)
        if match and match.group(2) == value:
            assigned.add(match.group(1))
    return assigned


def _refs_var(text, name):
    return bool(re.search(r"(\$" + re.escape(name) + r"\b|\$\{" + re.escape(name) + r"\})", text or ""))


def _has_indirect_dynamic_commit(line):
    try:
        toks = _tokens(_normalize_command(line))
    except ValueError:
        return False
    assigned = _commit_assignment_vars(toks)
    if not assigned:
        return False
    for i, tok in enumerate(toks):
        if any(_refs_var(tok, name) for name in assigned) and _at_cmd(toks, i):
            return True
        base = os.path.basename(tok)
        if base in SHELL_EXECUTORS and _at_cmd(toks, i):
            nested = _shell_c_arg(toks, i)
            if any(_refs_var(nested, name) for name in assigned):
                return True
    return False


def _has_variable_expanded_git_commit(toks):
    git_vars = _literal_assignment_vars(toks, "git")
    commit_vars = _literal_assignment_vars(toks, "commit")
    if not git_vars and not commit_vars:
        return False
    for i, tok in enumerate(toks):
        if git_vars and any(_refs_var(tok, name) for name in git_vars) and _at_cmd(toks, i):
            synthetic = ["git", *toks[i + 1:]]
            subcommand, _root_option = _git_subcommand(synthetic, 0, HOOK_CWD, commit_vars=commit_vars)
            if subcommand == "commit":
                return True
        if os.path.basename(tok) == "git" and _at_cmd(toks, i):
            subcommand, _root_option = _git_subcommand(toks, i, HOOK_CWD, commit_vars=commit_vars)
            if subcommand == "commit":
                return True
    return False


def _tokens_contain_git_commit(tokens):
    for j, tok in enumerate(tokens[:-1]):
        if os.path.basename(tok) == "git" and tokens[j + 1] == "commit":
            return True
    return False


def _segment_scan_result(segment):
    if not segment:
        return None
    return scan_line(" ".join(shlex.quote(tok) for tok in segment))


def _has_argv_executor_commit(toks):
    for i, tok in enumerate(toks):
        base = os.path.basename(tok)
        if base in ARGV_EXECUTORS and _at_cmd(toks, i):
            j = i + 1
            segment = []
            while j < len(toks) and toks[j] not in SEPS:
                segment.append(toks[j])
                j += 1
            if _tokens_contain_git_commit(segment) or _segment_scan_result(segment):
                return True
        if base == "find" and _at_cmd(toks, i):
            j = i + 1
            while j < len(toks) and toks[j] not in SEPS:
                if toks[j] in {"-exec", "-execdir"}:
                    k = j + 1
                    segment = []
                    while k < len(toks) and toks[k] not in {";", "+", ";;"}:
                        segment.append(toks[k])
                        k += 1
                    if _tokens_contain_git_commit(segment) or _segment_scan_result(segment):
                        return True
                    j = k
                j += 1
    return False


def _has_unsupported_compound_commit(line):
    if not (re.search(r"\bgit\b", line) and re.search(r"\bcommit\b", line)):
        return False
    return bool(
        re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\(\)\s*\{", line)
        or re.search(r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\b.*\{", line)
    )


def scan_line(line):
    line = _normalize_command(line)
    if _has_unsupported_compound_commit(line):
        return "parse-error"
    if _has_indirect_dynamic_commit(line):
        return "parse-error"
    if _has_unquoted_substitution_commit(line):
        return "parse-error"
    try:
        toks = _tokens(line)
    except ValueError:
        return "parse-error" if re.search(r"\bgit\b", line) and re.search(r"\bcommit\b", line) else None
    if _has_argv_executor_commit(toks):
        return "parse-error"
    if _has_variable_expanded_git_commit(toks):
        return "parse-error"
    cwd_changed = False
    current_cwd = os.path.abspath(HOOK_CWD)
    cwd_stack = []
    for i, tok in enumerate(toks):
        base = os.path.basename(tok)
        if tok == "(" and _at_cmd(toks, i):
            cwd_stack.append((cwd_changed, current_cwd))
            continue
        if tok in {")", ");"} and cwd_stack:
            cwd_changed, current_cwd = cwd_stack.pop()
            continue
        if base in {"cd", "pushd", "popd"} and _at_cmd(toks, i):
            cwd_changed = True
            if base in {"cd", "pushd"}:
                next_cwd = _cd_target(toks, i, current_cwd)
                current_cwd = next_cwd or current_cwd
            else:
                current_cwd = HOOK_CWD
            continue
        if base in SHELL_DYNAMIC_EXECUTORS and _at_cmd(toks, i):
            parts = _dynamic_shell_parts(toks, i)
            payload = " ".join(parts)
            source_state = (
                _source_target_state(parts, current_cwd, _literal_assignments_before(toks, i))
                if base in {"source", "."}
                else ""
            )
            if base in {"source", "."} and cwd_changed and source_state == "commit":
                return "unsafe-cwd-change"
            nested_result = scan_line(payload) if base == "eval" and payload else None
            if nested_result:
                return "unsafe-cwd-change" if cwd_changed else nested_result
            if re.search(r"\bgit\b", payload) and re.search(r"\bcommit\b", payload):
                return "parse-error"
            if base == "eval" and re.search(r"\bgit\b", line) and re.search(r"\bcommit\b", line):
                return "parse-error"
            if base in {"source", "."} and (
                source_state == "commit"
                or (source_state == "unknown" and re.search(r"\bgit\b", line) and re.search(r"\bcommit\b", line))
            ):
                return "parse-error"
        if base in SHELL_EXECUTORS and _at_cmd(toks, i):
            prefix = _segment_prefix(toks, i)
            if _shell_receives_stdin(toks, i) and re.search(r"\bgit\b", line) and re.search(r"\bcommit\b", line):
                return "parse-error"
            nested = _shell_c_arg(toks, i)
            nested_result = scan_line(nested) if nested else None
            if nested_result:
                return "unsafe-cwd-change" if (cwd_changed or _prefix_has_cwd_change(prefix)) else nested_result
        if base == "env" and _at_cmd(toks, i):
            for nested in _env_split_args(toks, i):
                nested_result = scan_line(nested)
                if nested_result:
                    return "unsafe-cwd-change" if cwd_changed else nested_result
        if base == "git" and _at_cmd(toks, i):
            prefix = _segment_prefix(toks, i)
            prefix_cwd = _prefix_cwd(prefix, current_cwd)
            subcommand, root_option = _git_subcommand(toks, i, prefix_cwd, _git_env_aliases(prefix))
            if subcommand == "commit":
                if cwd_changed or _prefix_has_cwd_change(prefix):
                    return "unsafe-cwd-change"
                if root_option or _prefix_has_git_root_env(prefix):
                    return "unsafe-root-option"
                return "commit"
    return None


_raw_command = _normalize_command(os.environ.get("COMMAND", ""))
if _has_executable_heredoc_commit(_raw_command):
    print("parse-error")
    raise SystemExit(0)

_command = _strip_heredoc_bodies(_raw_command)
if _has_multiline_indirect_eval_commit(_command):
    print("parse-error")
    raise SystemExit(0)

_scan_text = " ; ".join(line for line in _command.splitlines() if line.strip())
result = scan_line(_scan_text)
if result:
    print(result)
PY
)
[ -n "$HIT" ] || exit 0
if [ "$HIT" = "unsafe-root-option" ]; then
  echo "BLOCKED: Guru commit guard detected git commit with repository-changing options or environment." >&2
  echo "Run git commit from the target Trellis project root so check-commit validates the correct task." >&2
  exit 2
fi
if [ "$HIT" = "unsafe-cwd-change" ]; then
  echo "BLOCKED: Guru commit guard detected git commit after an in-command cwd change." >&2
  echo "Run git commit from the target Trellis project root so check-commit validates the correct task." >&2
  exit 2
fi
if [ "$HIT" = "parse-error" ]; then
  echo "BLOCKED: Guru commit guard could not safely parse a command containing git commit." >&2
  echo "Run guru_gate.py check-commit manually, then rerun git commit from the Trellis project root." >&2
  exit 2
fi

PROJECT_DIR="${HOOK_CWD:-${CLAUDE_PROJECT_DIR:-${CODEX_PROJECT_DIR:-.}}}"
find_project_root() (
  local dir="${1:-.}"
  cd "$dir" 2>/dev/null || return 1
  while true; do
    if [ -d ".trellis" ]; then
      pwd
      return 0
    fi
    [ "$PWD" = "/" ] && return 1
    cd ..
  done
)

ROOT_DIR=""
for candidate in "$PROJECT_DIR" "$HOOK_CWD" "."; do
  if ROOT_DIR=$(find_project_root "$candidate" 2>/dev/null); then
    break
  fi
done
if [ -z "$ROOT_DIR" ]; then
  echo "BLOCKED: Guru commit guard detected git commit but cannot locate project .trellis root." >&2
  exit 2
fi
cd "$ROOT_DIR" 2>/dev/null || { echo "BLOCKED: cannot enter Guru project root: $ROOT_DIR" >&2; exit 2; }
[ -f ".trellis/scripts/guru/guru_gate.py" ] || { echo "BLOCKED: Guru commit guard cannot find .trellis/scripts/guru/guru_gate.py" >&2; exit 2; }

# No active Guru task candidate means this hook has nothing to protect.
# Keep this before check-commit so ordinary commits in freshly installed Guru
# repos are not blocked just because there is no task yet.
if ! python3 - <<'PY'
import json
import os
import sys

tasks_root = os.path.join(".trellis", "tasks")
if not os.path.isdir(tasks_root):
    sys.exit(1)
for name in os.listdir(tasks_root):
    task_json = os.path.join(tasks_root, name, "task.json")
    if not os.path.isfile(task_json):
        continue
    try:
        with open(task_json, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        continue
    if isinstance(data, dict) and data.get("status") in {"planning", "in_progress"}:
        sys.exit(0)
sys.exit(1)
PY
then
  exit 0
fi

if ! python3 .trellis/scripts/guru/guru_gate.py check-commit >&2; then
  echo "BLOCKED: Guru task is not ready to commit." >&2
  echo "Run guru_gate.py status <task-dir>; if START_READY, run task.py start first." >&2
  exit 2
fi
exit 0
