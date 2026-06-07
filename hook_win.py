#!/usr/bin/env python3
"""Claude Code status hook for Windows — replaces hook.sh.

Normal usage (called by Claude Code hooks):
    python hook_win.py <state>        state = working|confirm|done|idle

Installer helper:
    python hook_win.py --install  <src_dir>    register hooks in settings.json
    python hook_win.py --uninstall             remove hooks from settings.json
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

HOME = Path.home()
STATE_FILE = HOME / ".claude" / "cc-status.json"
ASSETS = Path(__file__).parent / "assets"

# ---------------------------------------------------------------------------
# Installer / uninstaller
# ---------------------------------------------------------------------------

def _hook_cmd(src: Path) -> str:
    python_exe = src / ".venv" / "Scripts" / "python.exe"
    hook_script = src / "hook_win.py"
    return f'"{python_exe}" "{hook_script}"'


def install(src: Path):
    settings = HOME / ".claude" / "settings.json"
    try:
        cfg = json.loads(settings.read_text(encoding="utf-8"))
    except Exception:
        cfg = {}

    hooks = cfg.setdefault("hooks", {})
    base_cmd = _hook_cmd(src)
    spec = {
        "UserPromptSubmit": ("working", None),
        "PreToolUse":       ("working", "*"),
        "Notification":     ("confirm", None),
        "Stop":             ("done",    None),
        "SessionEnd":       ("idle",    None),
    }
    for ev, (state, matcher) in spec.items():
        cmd = f"{base_cmd} {state}"
        arr = hooks.setdefault(ev, [])
        if any(h.get("command") == cmd for e in arr for h in e.get("hooks", [])):
            continue
        entry = {"hooks": [{"type": "command", "command": cmd}]}
        if matcher:
            entry["matcher"] = matcher
        arr.append(entry)

    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  hooks registered ok")


def uninstall():
    settings = HOME / ".claude" / "settings.json"
    try:
        cfg = json.loads(settings.read_text(encoding="utf-8"))
    except Exception:
        return
    hooks = cfg.get("hooks", {})
    marker = "hook_win.py"
    for ev in list(hooks.keys()):
        hooks[ev] = [
            e for e in hooks[ev]
            if not any(marker in h.get("command", "") for h in e.get("hooks", []))
        ]
        if not hooks[ev]:
            del hooks[ev]
    settings.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  hooks removed ok")


# ---------------------------------------------------------------------------
# Normal hook operation
# ---------------------------------------------------------------------------

def write_state(state: str):
    """Atomic write so systray.py never reads a half-written file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"state": state, "ts": int(time.time())})
    fd, tmp = tempfile.mkstemp(dir=STATE_FILE.parent, suffix=".tmp")
    try:
        os.write(fd, payload.encode())
        os.close(fd)
        os.replace(tmp, STATE_FILE)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def play_sound(state: str):
    """Spawn a detached process to play the chime so the hook returns fast."""
    sounds = {"confirm": "confirm.mp3", "done": "done.mp3"}
    fname = sounds.get(state)
    if not fname:
        return
    path = ASSETS / fname
    if not path.exists():
        return
    import subprocess
    # Spawn a fresh Python process that plays the file then exits.
    # DETACHED_PROCESS keeps it alive after the hook process exits.
    subprocess.Popen(
        [sys.executable, "-c",
         f"from playsound import playsound; playsound(r'{path}')"],
        creationflags=0x00000008 | 0x08000000,  # DETACHED_PROCESS | CREATE_NO_WINDOW
        close_fds=True,
    )


def drain_stdin():
    """Claude pipes the hook JSON payload on stdin; drain it without blocking."""
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if args and args[0] == "--install":
        src = Path(args[1]) if len(args) > 1 else Path(__file__).parent
        install(src)
        sys.exit(0)

    if args and args[0] == "--uninstall":
        uninstall()
        sys.exit(0)

    state = args[0] if args else "idle"
    drain_stdin()
    write_state(state)
    play_sound(state)
