<h1 align="center">🤖 ClaudeMood</h1>

<p align="center">
  <b>See what Claude Code is doing — without alt-tabbing to the terminal.</b><br/>
  A little Claude lives in your macOS menu bar and reacts as it works, waits, and finishes.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-13%2B-black?logo=apple" alt="macOS">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
  <img src="https://img.shields.io/github/stars/kellysun2258741977-source/claude-mood?style=social" alt="stars">
</p>

<p align="center">
  <!-- Record this with ./demo.sh + Kap — see "Recording the demo GIF" below -->
  <img src="assets/demo.gif" width="600" alt="ClaudeMood cycling through working / needs-you / done states in the menu bar">
</p>

## Why

I kept alt-tabbing to my terminal just to check whether Claude Code was still
working or waiting on me. So I put its status in my menu bar — one glance, no
context switch. An animated Claude shows the state, and a soft chime nudges you
the moment it needs you.

## States

| | State | What it means |
|---|---|---|
| 🟡 | **Working** | Claude is thinking / running tools |
| 🔴 | **Needs you** | Waiting for a permission or your input — *plays a chime* |
| 🟢 | **Done** | Finished the turn — *plays a chime* |
| ⚪️ | **Idle** | Nothing running |

## Install

**macOS**

```bash
git clone https://github.com/kellysun2258741977-source/claude-mood ~/claude-mood
cd ~/claude-mood && ./install.sh
```

Claude appears in your menu bar and **starts on every login**.
Quit anytime from the menu (**Quit Claude Status**); remove with `./uninstall.sh`.

**Windows**

1. Install [Python 3.8+](https://python.org) — check **"Add Python to PATH"** during setup
2. Clone the repo and double-click `install_win.bat`

```
git clone https://github.com/kellysun2258741977-source/claude-mood
cd claude-mood
install_win.bat
```

Claude appears in your **system tray** (bottom-right, near the clock) and starts on every login.
Remove with `uninstall_win.bat`.

<sub>Both installers create a self-contained `venv` (never touch your global Python) and
**append** hooks to `~/.claude/settings.json` without overwriting your existing ones.</sub>

## How it works

```
Claude Code hooks ──▶ ~/.claude/cc-status.json ──▶ menu-bar app polls & animates
 (UserPromptSubmit/PreToolUse → working, Notification → needs-you,
  Stop → done, SessionEnd → idle)
```

A ~120-line menu-bar app ([`menubar.py`](menubar.py)) polls a small state file
that the hooks write. No daemon framework, no magic.

## Privacy & Security

- **No network calls.** It only reads/writes local files under `~/.claude/`.
- **No telemetry, no API keys, no `--dangerously-skip-permissions`.**
- The hook is a tiny shell script ([`hook.sh`](hook.sh)) that writes one line of
  JSON and plays a local sound. Read every line yourself — it's all here.

## Customize

Drop your own art/sounds into `assets/` — any GIF/PNG and any `.mp3` works:

| File | Shown when |
|---|---|
| `assets/claude-fu.gif` | working |
| `assets/claude-loading.gif` | needs you |
| `assets/claude-sparkle.gif` | done |
| `assets/claude-fail.png` | idle |
| `assets/confirm.mp3` / `assets/done.mp3` | sounds |

Per-state size/alignment is auto-handled (artwork is cropped to its content and
centered), so any image just works.

## Requirements

macOS · `python3` (the installer builds its own venv for `Pillow` + `pyobjc`).

## Recording the demo GIF

```bash
./demo.sh        # cycles working → needs-you → done → idle with pauses
```
1. Install [Kap](https://getkap.co) (free, no watermark).
2. Start a Kap recording over the **menu-bar area** (top-right).
3. Run `./demo.sh` and let it cycle (~20s).
4. Crop tight to the icon, export as GIF (<5 MB), save as `assets/demo.gif`.

## Credits

Emoji are community artwork from [EmojiBox](https://www.emojibox.app/topics/claude);
notification chimes are Claude's own UI sounds. For personal use.

## License

[MIT](LICENSE)
