"""Exits 1 when a shell command would push to main; 0 otherwise.

Delminio's hook runs it before every command matching `git*push*`, with the
CLI's event JSON on stdin. A git push it can't parse counts as a push to
main: the decision stops by mistake rather than lets through by mistake.
Heredoc bodies are skipped, so a commit message that mentions a push passes.
"""
import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED = "main"
# git push options that take a separate value.
OPTS_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}


def current_branch(cwd):
    out = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                         capture_output=True, text=True, timeout=3)
    return out.stdout.strip() if out.returncode == 0 else None


def pushes_to_main(tokens, cwd):
    """tokens start right after `git`."""
    i = 0
    while i < len(tokens) and tokens[i] != "push":
        if tokens[i] == "-C" and i + 1 < len(tokens):
            cwd = os.path.join(cwd, tokens[i + 1])
            i += 2
            continue
        i += 1
    if i == len(tokens):
        return False
    positional = []
    args = tokens[i + 1:]
    j = 0
    while j < len(args):
        a = args[j]
        if a in ("--all", "--mirror"):
            return True
        if a in OPTS_WITH_VALUE:
            j += 2
            continue
        if not a.startswith("-"):
            positional.append(a)
        j += 1
    refspecs = positional[1:]
    branch = current_branch(cwd)
    if not refspecs:
        return branch in (PROTECTED, None)
    for spec in refspecs:
        dst = spec.lstrip("+").split(":")[-1].removeprefix("refs/heads/")
        if dst == PROTECTED or (dst == "HEAD" and branch in (PROTECTED, None)):
            return True
    return False


def without_heredocs(command):
    """Drops heredoc bodies: they are text (a commit message), not commands."""
    kept, delimiter = [], None
    for line in command.split("\n"):
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        kept.append(line)
        found = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", line)
        if found:
            delimiter = found.group(1)
    return "\n".join(kept)


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    command = (event.get("tool_input") or {}).get("command") or os.environ.get("DELMINIO_COMANDO", "")
    cwd = event.get("cwd") or os.environ.get("DELMINIO_CWD") or os.getcwd()
    for segment in re.split(r"&&|\|\||;|\||\n", without_heredocs(command)):
        try:
            tokens = shlex.split(segment)
            for k, t in enumerate(tokens):
                if os.path.basename(t) == "git" and pushes_to_main(tokens[k + 1:], cwd):
                    print(f"push to {PROTECTED} needs Sarah's ok: {segment.strip()}")
                    return 1
        except (ValueError, subprocess.SubprocessError):
            # Unreadable text is only a risk when it is a git push.
            if re.search(r"(^|[\s/])git\s(.*\s)?push\b", segment):
                print(f"could not read the command, treated as a push to {PROTECTED}: {segment.strip()}")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
