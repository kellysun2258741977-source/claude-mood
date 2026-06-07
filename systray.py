#!/usr/bin/env python3
"""ClaudeMood system tray app for Windows.

Reads ~/.claude/cc-status.json (written by hook_win.py) and shows an animated
Claude emoji per state. GIF frames are cycled via a background thread.

Requires: Pillow, pystray  (installed by install_win.bat)
"""
import json
import sys
import time
import threading
from pathlib import Path

from PIL import Image, ImageSequence
import pystray

HOME = Path.home()
STATE_FILE = HOME / ".claude" / "cc-status.json"
ASSETS = Path(__file__).parent / "assets"

SOURCES = {
    "working": "claude-fu.gif",
    "confirm": "claude-loading.gif",
    "done":    "claude-sparkle.gif",
    "idle":    "claude-fail.png",
}

DONE_TIMEOUT = 30   # seconds after "done" -> fall back to "idle"
POLL = 0.1          # animation + state poll interval in seconds
ICON_SIZE = 32      # Windows tray icon size in pixels


def load_frames(path):
    """Load a GIF/PNG, crop transparent padding, fit to ICON_SIZE, return RGBA list."""
    frames = []
    try:
        img = Image.open(path)
        for frame in ImageSequence.Iterator(img):
            f = frame.convert("RGBA")
            bbox = f.getchannel("A").getbbox()
            if bbox:
                f = f.crop(bbox)
            # fit inside ICON_SIZE x ICON_SIZE, preserve aspect ratio
            f.thumbnail((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
            canvas = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
            x = (ICON_SIZE - f.width) // 2
            y = (ICON_SIZE - f.height) // 2
            canvas.alpha_composite(f, (x, y))
            frames.append(canvas)
    except Exception as e:
        print(f"warning: could not load {path}: {e}", file=sys.stderr)
    # fallback: grey square so the tray always shows something
    return frames or [Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (180, 180, 180, 255))]


def read_state():
    """Return (state_str, unix_ts). Falls back to ('idle', 0) on any error."""
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data.get("state", "idle"), float(data.get("ts", 0))
    except Exception:
        return "idle", 0.0


def animate(icon, frames):
    """Background thread: poll state file and cycle frames."""
    state = "idle"
    idx = 0
    done_since = None

    while True:
        raw_state, ts = read_state()

        # done -> idle timeout
        if raw_state == "done":
            if state != "done":
                done_since = time.time()
            elif done_since and (time.time() - done_since) > DONE_TIMEOUT:
                raw_state = "idle"
        else:
            done_since = None

        # safe fallback for unknown states
        if raw_state not in frames:
            raw_state = "idle"

        changed = raw_state != state
        if changed:
            state = raw_state
            idx = 0

        state_frames = frames[state]
        if changed or len(state_frames) > 1:
            icon.icon = state_frames[idx % len(state_frames)]
            icon.title = f"ClaudeMood: {state}"

        idx += 1
        time.sleep(POLL)


def main():
    # Pre-load all state artwork
    frames = {s: load_frames(ASSETS / f) for s, f in SOURCES.items()}

    menu = pystray.Menu(
        pystray.MenuItem("Quit ClaudeMood", lambda icon, _: icon.stop())
    )
    icon = pystray.Icon(
        "ClaudeMood",
        frames["idle"][0],
        "ClaudeMood: idle",
        menu,
    )

    t = threading.Thread(target=animate, args=(icon, frames), daemon=True)
    t.start()

    icon.run()


if __name__ == "__main__":
    main()
