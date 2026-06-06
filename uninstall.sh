#!/bin/bash
# cc-status uninstaller: stops the app, removes autostart, hooks, and files.
set -uo pipefail

DIR="$HOME/.claude/cc-status"
PLIST="$HOME/Library/LaunchAgents/com.cc-status.menubar.plist"

echo "==> Stopping app + removing autostart"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
pkill -f menubar.py 2>/dev/null || true

echo "==> Removing our hooks from ~/.claude/settings.json (leaves your other hooks)"
python3 <<'PY'
import json, os
p = os.path.expanduser("~/.claude/settings.json")
try:
    cfg = json.load(open(p))
except (FileNotFoundError, ValueError):
    cfg = None
if cfg and "hooks" in cfg:
    for ev in list(cfg["hooks"]):
        cfg["hooks"][ev] = [e for e in cfg["hooks"][ev]
                            if "cc-status/hook.sh" not in json.dumps(e)]
        if not cfg["hooks"][ev]:
            del cfg["hooks"][ev]
    if not cfg["hooks"]:
        del cfg["hooks"]
    json.dump(cfg, open(p, "w"), indent=2, ensure_ascii=False)
print("    hooks cleaned")
PY

echo "==> Removing files"
rm -rf "$DIR"
rm -f "$HOME/.claude/cc-status.json"
echo "==> Uninstalled."
