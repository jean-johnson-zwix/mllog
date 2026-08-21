#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
# Deliberately no dependencies: this launcher is stdlib-only. The mllog pin lives
# in requirements.txt, which is also the stamp the bootstrap diffs against. Adding
# it here would fork the environment - `uv run --script` would build its own, while
# the hooks keep using ${CLAUDE_PLUGIN_DATA}/venv, installing mllog twice.
"""Self-bootstrapping MCP server launcher.

Invoked from .mcp.json. Deliberately Python, not shell: on Windows, Claude Code
resolves `bash` to WSL's bash, whose $HOME is /home/<user> - it cannot see the
Windows-side plugin dirs, so any bash launcher silently globs to nothing.

Discovery is anchored on a single choice: pick the cache entry with the highest
*parsed* version, then derive the data dir from that entry's marketplace. Both
halves therefore always come from the same install.

stdout is the MCP protocol channel. Everything diagnostic goes to stderr.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
PLUGINS = os.path.join(HOME, ".claude", "plugins")
# Names whose values never get written to the env probe artifact.
SENSITIVE = re.compile(
    r"TOKEN|KEY|SECRET|PASSWORD|PASSWD|AUTH|CREDENTIAL|COOKIE|SESSION", re.I
)


def log(msg):
    # Windows consoles are often cp1252; a non-encodable char in a path would
    # otherwise raise UnicodeEncodeError out of a diagnostic call.
    try:
        sys.stderr.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    print(f"mllog: {msg}", file=sys.stderr)


def die(msg):
    log(msg)
    sys.exit(1)


def version_key(version):
    """Parsed ordering, so 1.10.0 > 1.9.0. Lexicographic sort gets this wrong."""
    return tuple(int(n) for n in re.findall(r"\d+", version)) or (0,)


def discover():
    """Return (plugin_root, marketplace) for the newest installed mllog."""
    pattern = os.path.join(PLUGINS, "cache", "*", "mllog", "*", "requirements.txt")
    found = [os.path.normpath(p) for p in glob.glob(pattern)]
    if not found:
        die(f"no mllog plugin found under {os.path.join(PLUGINS, 'cache')}")

    def parts(path):
        # .../cache/<marketplace>/mllog/<version>/requirements.txt
        bits = path.split(os.sep)
        return bits[-4], bits[-2]  # marketplace, version

    best = max(found, key=lambda p: (version_key(parts(p)[1]), p))
    marketplace, version = parts(best)

    others = {parts(p)[0] for p in found} - {marketplace}
    if others:
        log(
            f"multiple mllog cache candidates found; selected marketplace "
            f"'{marketplace}' because version {version} is highest; also present: "
            f"{', '.join(sorted(others))} - remove the duplicate marketplace "
            f"registration to make this unambiguous"
        )
    return os.path.dirname(best), marketplace


def env_probe(data):
    """One-shot diagnostic: what plugin identity does the host actually pass?

    Values are written only for plugin-identifying names, and never for names
    that look like credentials - the name alone answers the question.
    """
    path = os.path.join(data, "mcp-env-probe.txt")
    if os.path.exists(path):
        return
    try:
        os.makedirs(data, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# Environment of the MCP server process, as passed by the host.\n")
            fh.write("# Values shown only for plugin-identifying, non-sensitive names.\n")
            fh.write(f"# cwd: {os.getcwd()}\n\n")
            for name in sorted(os.environ):
                identifying = name.startswith(("CLAUDE", "MLLOG", "MCP", "PLUGIN"))
                show = identifying and not SENSITIVE.search(name)
                fh.write(f"{name}={os.environ[name] if show else '<redacted>'}\n")
        log(f"wrote one-shot env probe to {path}")
    except OSError as exc:
        log(f"env probe failed (non-fatal): {exc}")


def venv_python(venv):
    for rel in ("Scripts/python.exe", "bin/python"):
        path = os.path.join(venv, *rel.split("/"))
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


root, marketplace = discover()
req = os.path.join(root, "requirements.txt")
# Honour the host's own value when it supplies one; otherwise pair with the
# marketplace we just selected, so venv and requirements.txt always match.
data = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
    PLUGINS, "data", f"mllog-{marketplace}"
)

env_probe(data)

venv = os.path.join(data, "venv")
stamp = os.path.join(venv, ".requirements.txt")
python = venv_python(venv)

if not (python and read(req) == read(stamp) and importable(python)):
    log("bootstrapping venv...")
    os.makedirs(os.path.dirname(venv), exist_ok=True)
    # stdout is the protocol channel - route subprocess stdout to stderr rather
    # than trusting their --quiet flags to stay silent.
    quiet = {"stdout": sys.stderr, "check": True}
    try:
        if shutil.which("uv"):
            # uv creates minimal venvs (no pip) - use uv for both venv and install
            if not python:
                subprocess.run(["uv", "venv", venv, "--quiet"], **quiet)
            subprocess.run(
                ["uv", "pip", "install", "--quiet", "-r", req],
                env={**os.environ, "VIRTUAL_ENV": venv}, **quiet,
            )
        else:
            if not python:
                subprocess.run([sys.executable, "-m", "venv", venv], **quiet)
            python = venv_python(venv)
            subprocess.run([python, "-m", "pip", "install", "-q", "-r", req], **quiet)
    except (subprocess.CalledProcessError, OSError) as exc:
        die(f"bootstrap failed - {exc}")

    python = venv_python(venv)
    if not (python and importable(python)):
        if os.path.isfile(stamp):
            os.remove(stamp)
        die("bootstrap failed - mllog.mcp_server not importable")
    with open(stamp, "wb") as fh:
        fh.write(read(req))

# Stay alive as a thin parent rather than os.execv: on Windows execv exits the
# parent, and Claude Code reads that as the server dying. stdio is inherited.
sys.exit(subprocess.run([python, "-m", "mllog.mcp_server"]).returncode)
