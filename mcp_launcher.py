#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Self-bootstrapping MCP server launcher for the mllog plugin.

Claude Code sets CLAUDE_PLUGIN_ROOT and CLAUDE_PLUGIN_DATA in the MCP server's
*process environment*. Note they are NOT usable as ${...} inside .mcp.json - that
text is template-expanded before any process exists, which fails. Read them here.

Python, not shell: on Windows `bash` resolves to WSL, which cannot see the
Windows-side plugin dirs. stdout is the MCP protocol channel, so every
diagnostic - including subprocess output - goes to stderr.
"""
import glob
import os
import re
import shutil
import subprocess
import sys


def log(msg):
    print(f"mllog: {msg}", file=sys.stderr)


def plugin_root():
    """The install being launched. The host names it; glob only when run by hand."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        return os.path.normpath(root)
    found = glob.glob(os.path.expanduser(
        "~/.claude/plugins/cache/*/mllog/*/requirements.txt"))
    if not found:
        log("no mllog install found; set CLAUDE_PLUGIN_ROOT")
        sys.exit(1)
    # Parsed ordering, so 1.10.0 outranks 1.9.0 as lexicographic sort does not.
    def version(path):
        return [int(n) for n in re.findall(r"\d+", os.path.basename(os.path.dirname(path)))]
    return os.path.normpath(os.path.dirname(max(found, key=version)))


def venv_python(venv):
    for name in ("Scripts/python.exe", "bin/python"):
        path = os.path.join(venv, *name.split("/"))
        if os.path.isfile(path):
            return path
    return None


def importable(python):
    return subprocess.run(
        [python, "-c", "import mllog.mcp_server"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def read(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


root = plugin_root()
req = os.path.join(root, "requirements.txt")
# Paired with root by the host; derived from its marketplace when running by hand.
data = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser(
    f"~/.claude/plugins/data/mllog-{root.split(os.sep)[-3]}")

venv = os.path.join(data, "venv")
stamp = os.path.join(venv, ".requirements.txt")
python = venv_python(venv)

if not (python and read(req) == read(stamp) and importable(python)):
    log("bootstrapping venv...")
    os.makedirs(data, exist_ok=True)
    # stdout is the protocol channel - never let a subprocess write to it.
    quiet = {"stdout": sys.stderr, "check": True}
    try:
        if shutil.which("uv"):
            # uv creates minimal venvs (no pip), so use uv for the install too.
            if not python:
                subprocess.run(["uv", "venv", venv, "--quiet"], **quiet)
            subprocess.run(["uv", "pip", "install", "--quiet", "-r", req],
                           env={**os.environ, "VIRTUAL_ENV": venv}, **quiet)
        else:
            if not python:
                subprocess.run([sys.executable, "-m", "venv", venv], **quiet)
            subprocess.run([venv_python(venv), "-m", "pip", "install", "-q", "-r", req],
                           **quiet)
    except (subprocess.CalledProcessError, OSError) as exc:
        log(f"bootstrap failed - {exc}")
        sys.exit(1)

    python = venv_python(venv)
    if not (python and importable(python)):
        if os.path.isfile(stamp):
            os.remove(stamp)
        log("bootstrap failed - mllog.mcp_server not importable")
        sys.exit(1)
    with open(stamp, "wb") as fh:
        fh.write(read(req))

# A thin live parent, not os.execv: on Windows execv exits the parent, which the
# host reads as the server dying. stdio is inherited by the child.
sys.exit(subprocess.run([python, "-m", "mllog.mcp_server"]).returncode)
