#!/usr/bin/env python3
"""Claude Code status indicator in the macOS menu bar (pure AppKit).

Reads ~/.claude/cc-status.json (written by hook.sh) and shows an animated
Claude emoji per state. Replicates the claude-lamp idea:
hooks -> state file -> a polling app that drives the indicator.
"""
import io
import json
import math
import os
import sys
import time

import objc
from PIL import Image, ImageSequence
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSImage,
    NSMenu,
    NSMenuItem,
)
from Foundation import NSObject, NSTimer, NSData, NSMakeSize

HOME = os.path.expanduser("~")
STATE_FILE = os.path.join(HOME, ".claude", "cc-status.json")
ASSETS = os.path.join(HOME, ".claude", "cc-status", "assets")
PIDFILE = os.path.join(HOME, ".claude", "cc-status", ".pid")


def ensure_single_instance():
    """Exit quietly if another instance is already running (autostart + manual)."""
    if os.path.exists(PIDFILE):
        try:
            os.kill(int(open(PIDFILE).read()), 0)
            sys.exit(0)  # alive -> we're the duplicate
        except (ValueError, ProcessLookupError):
            pass  # stale pidfile, take over
    with open(PIDFILE, "w") as fh:
        fh.write(str(os.getpid()))

# state -> source emoji file (user-picked)
SOURCES = {
    "working": "claude-fu.gif",       # 工作中
    "confirm": "claude-loading.gif",  # 需确认
    "done": "claude-sparkle.gif",     # 已完成
    "idle": "claude-fail.png",        # 闲暇中 (static)
}
DONE_TIMEOUT = 30   # seconds after "done" -> fall back to "idle"
CANVAS_H = 44       # icon canvas height in px (= 22pt @2x retina)
SCALE = 2           # px per point
POLL = 0.1          # state poll + animation tick (seconds)

# per-state artwork peak height in px, tuned so the 4 states look balanced
# (working is the reference; the others are smaller so none looks oversized)
TARGET = {"working": 38, "confirm": 30, "done": 30, "idle": 30}


def load_frames(src, target):
    """Load a gif/png into in-memory NSImages on a fixed CANVAS_H-tall canvas.

    Each frame is cropped to its OWN content and centered (stable vertical
    alignment, no drifting low), then scaled by one fixed factor derived from
    the union bbox so the artwork peaks at `target` px without per-frame size
    jitter. Per-state `target` keeps the states visually balanced.
    """
    frames = [fr.convert("RGBA") for fr in ImageSequence.Iterator(Image.open(src))]
    union = None
    for f in frames:
        bb = f.getchannel("A").getbbox()
        if bb:
            union = bb if union is None else (
                min(union[0], bb[0]), min(union[1], bb[1]),
                max(union[2], bb[2]), max(union[3], bb[3]),
            )
    if union is None:  # fully transparent source -> use full canvas
        union = (0, 0, frames[0].width, frames[0].height)
    factor = target / (union[3] - union[1])
    cw = math.ceil((union[2] - union[0]) * factor) + 2
    out = []
    for f in frames:
        canvas = Image.new("RGBA", (cw, CANVAS_H), (0, 0, 0, 0))
        bb = f.getchannel("A").getbbox()
        if bb:
            c = f.crop(bb)
            nw = max(1, round(c.width * factor))
            nh = max(1, round(c.height * factor))
            c = c.resize((nw, nh), Image.LANCZOS)
            canvas.alpha_composite(c, ((cw - nw) // 2, (CANVAS_H - nh) // 2))
        buf = io.BytesIO()
        canvas.save(buf, "PNG")
        data = NSData.dataWithBytes_length_(buf.getvalue(), len(buf.getvalue()))
        img = NSImage.alloc().initWithData_(data)
        img.setSize_(NSMakeSize(cw / SCALE, CANVAS_H / SCALE))  # points = px / scale
        img.setTemplate_(False)  # keep emoji colors
        out.append(img)
    return out


class StatusApp(NSObject):
    def init(self):
        self = objc.super(StatusApp, self).init()
        self.frames = {
            s: load_frames(os.path.join(ASSETS, f), TARGET[s])
            for s, f in SOURCES.items()
        }
        self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        menu = NSMenu.alloc().init()
        menu.addItem_(
            NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit Claude Status", "terminate:", "q"
            )
        )
        self.item.setMenu_(menu)
        self.state = None
        self.idx = 0
        self.item.button().setImage_(self.frames["idle"][0])
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            POLL, self, "tick:", None, True
        )
        return self

    def read_state(self):
        try:
            with open(STATE_FILE) as fh:
                d = json.load(fh)
        except (FileNotFoundError, ValueError):
            return "idle"
        s = d.get("state", "idle")
        if s == "done" and time.time() - d.get("ts", 0) > DONE_TIMEOUT:
            return "idle"
        return s if s in self.frames else "idle"

    def tick_(self, _timer):
        s = self.read_state()
        changed = s != self.state
        if changed:
            self.state = s
            self.idx = 0
        frames = self.frames[self.state]
        if changed or len(frames) > 1:  # skip redundant redraws for static states
            self.item.button().setImage_(frames[self.idx % len(frames)])
            self.idx += 1


if __name__ == "__main__":
    ensure_single_instance()
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # no Dock icon
    _delegate = StatusApp.alloc().init()
    app.run()
