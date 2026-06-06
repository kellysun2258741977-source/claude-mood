#!/bin/bash
# Claude Code status hook -> writes current state to cc-status.json
# Usage: hook.sh <state>   state = working | confirm | done | idle
STATE="${1:-idle}"
OUT="$HOME/.claude/cc-status.json"
# Claude pipes the hook JSON on stdin; drain it but never hang on a tty
[ -t 0 ] || cat >/dev/null 2>&1
# atomic write so the menubar poller never reads a half-written file
TMP="$(mktemp "${OUT}.XXXXXX")"
printf '{"state":"%s","ts":%s}\n' "$STATE" "$(date +%s)" >"$TMP"
mv -f "$TMP" "$OUT"
# sounds play in background so the hook returns fast
if [ "$STATE" = "confirm" ]; then
  afplay "$HOME/.claude/cc-status/assets/confirm.mp3" >/dev/null 2>&1 &
elif [ "$STATE" = "done" ]; then
  afplay "$HOME/.claude/cc-status/assets/done.mp3" >/dev/null 2>&1 &
fi
