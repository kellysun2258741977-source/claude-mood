#!/bin/bash
# Drives the menu-bar indicator through every state so you can screen-record a
# demo GIF. Start your recorder (e.g. Kap) over the menu bar, then run this.
H="$HOME/.claude/cc-status/hook.sh"

echo "Start your screen recorder over the menu bar now."
for i in 3 2 1; do printf "  recording in %s...\r" "$i"; sleep 1; done
echo

bash "$H" working; echo "🟡 working";        sleep 4
bash "$H" confirm; echo "🔴 needs you (chime)"; sleep 4
bash "$H" working; echo "🟡 working";        sleep 3
bash "$H" done;    echo "🟢 done (chime)";    sleep 4
bash "$H" idle;    echo "⚪️ idle";           sleep 3

echo "Done — stop recording. Crop to the icon and export as assets/demo.gif"
