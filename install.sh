#!/bin/bash
# cc-status installer: one command sets up deps, hooks, autostart, and launches.
# Re-running is safe (idempotent).
set -euo pipefail

DIR="$HOME/.claude/cc-status"
SRC="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.cc-status.menubar.plist"

echo "==> Installing cc-status into $DIR"
mkdir -p "$DIR/assets"

# 1. copy app files if installing from a cloned repo (skip if already in place)
if [ "$SRC" != "$DIR" ]; then
  cp "$SRC/menubar.py" "$SRC/hook.sh" "$SRC/requirements.txt" "$DIR/"
  cp "$SRC/assets/"* "$DIR/assets/" 2>/dev/null || true
fi
chmod +x "$DIR/hook.sh"

# 2. self-contained venv for the menu-bar app (won't touch your global python)
echo "==> Creating venv + installing deps (Pillow, pyobjc)..."
python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q --upgrade pip
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"

# 3. register Claude Code hooks (append-only, never clobbers your existing hooks)
echo "==> Registering hooks in ~/.claude/settings.json"
DIR="$DIR" python3 <<'PY'
import json, os
DIR = os.environ["DIR"]
p = os.path.expanduser("~/.claude/settings.json")
try:
    cfg = json.load(open(p))
except (FileNotFoundError, ValueError):
    cfg = {}
hooks = cfg.setdefault("hooks", {})
spec = {"UserPromptSubmit": ("working", None), "PreToolUse": ("working", "*"),
        "Notification": ("confirm", None), "Stop": ("done", None),
        "SessionEnd": ("idle", None)}
for ev, (state, matcher) in spec.items():
    cmd = f"bash {DIR}/hook.sh {state}"
    arr = hooks.setdefault(ev, [])
    if any(h.get("command") == cmd for e in arr for h in e.get("hooks", [])):
        continue  # already registered
    entry = {"hooks": [{"type": "command", "command": cmd}]}
    if matcher:
        entry["matcher"] = matcher
    arr.append(entry)
json.dump(cfg, open(p, "w"), indent=2, ensure_ascii=False)
print("    hooks ok")
PY

# 4. LaunchAgent for autostart on login
echo "==> Installing LaunchAgent (autostart)"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.cc-status.menubar</string>
  <key>ProgramArguments</key>
  <array>
    <string>$DIR/.venv/bin/python</string>
    <string>$DIR/menubar.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
  <key>StandardOutPath</key><string>/tmp/cc-status.log</string>
  <key>StandardErrorPath</key><string>/tmp/cc-status.log</string>
</dict>
</plist>
EOF

# 5. (re)start cleanly
launchctl unload "$PLIST" 2>/dev/null || true
pkill -f menubar.py 2>/dev/null || true
rm -f "$DIR/.pid"
launchctl load -w "$PLIST"

echo "==> Done. The Claude emoji should be in your menu bar now."
echo "    Quit:   click the icon -> Quit Claude Status"
echo "    Remove: bash $DIR/uninstall.sh"
