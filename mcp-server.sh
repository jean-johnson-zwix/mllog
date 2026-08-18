#!/usr/bin/env bash
# Self-bootstrapping MCP server launcher.
# Creates/upgrades the venv if needed, then starts the server.
# Called from .mcp.json — no PATH or pre-existing venv required.
set -e

# --- Locate plugin dirs (with fallbacks if env vars unset) ---
D="${CLAUDE_PLUGIN_DATA:-$(ls -d "$HOME/.claude/plugins/data/mllog-"* 2>/dev/null | head -1)}"
R="${CLAUDE_PLUGIN_ROOT:+${CLAUDE_PLUGIN_ROOT}/requirements.txt}"
[ -f "$R" ] 2>/dev/null || R=$(ls "$HOME/.claude/plugins/cache/"*/mllog/*/requirements.txt 2>/dev/null | tail -1)

V="$D/venv"
S="$V/.requirements.txt"
P="$V/Scripts/python.exe"; [ -f "$P" ] || P="$V/bin/python"

# --- Fast path: stamp matches + module importable → start immediately ---
if [ -f "$P" ] && [ -f "$S" ] && diff -q "$R" "$S" >/dev/null 2>&1 \
   && "$P" -c "import mllog.mcp_server" 2>/dev/null; then
  exec "$P" -m mllog.mcp_server
fi

# --- Bootstrap or upgrade ---
echo "mllog: bootstrapping venv..." >&2
mkdir -p "$(dirname "$V")" 2>/dev/null || true

if command -v uv >/dev/null 2>&1; then
  # uv creates minimal venvs (no pip) — use uv for both venv + install
  [ -d "$V" ] || uv venv "$V" --quiet 2>/dev/null
  VIRTUAL_ENV="$V" uv pip install --quiet -r "$R"
else
  # stdlib venv includes pip
  [ -f "$P" ] || { python -m venv "$V" 2>/dev/null || python3 -m venv "$V"; }
  PIP="$V/Scripts/pip.exe"; [ -f "$PIP" ] || PIP="$V/bin/pip"
  "$PIP" install -q -r "$R"
fi

# Re-locate python after bootstrap (venv may have just been created)
P="$V/Scripts/python.exe"; [ -f "$P" ] || P="$V/bin/python"

# Verify and stamp
if "$P" -c "import mllog.mcp_server" 2>/dev/null; then
  cp "$R" "$S"
else
  echo "mllog: bootstrap failed — mllog.mcp_server not importable" >&2
  rm -f "$S"
  exit 1
fi

exec "$P" -m mllog.mcp_server
