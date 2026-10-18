# agent-setup

My shared AI-agent instructions and macOS terminal setup: Codex, Claude Code, Cursor Agent, OpenCode, Ghostty, and HerdR.

[Read the shared instructions → AGENTS.md](AGENTS.md)

| Path | Contents |
| --- | --- |
| `AGENTS.md` | One shared instruction source for the four agents |
| `codex/`, `cursor/`, `opencode/` | Safe settings and sanitized examples of private configs |
| `claude/` | Claude Code preferences |
| `ghostty/` | Theme, HerdR startup, Mac keyboard shortcuts |
| `herdr/` | Terminal settings and colour-environment fix |
| `herdr-auto-title/` | Tab-only automatic title settings |
| `shell/` | Sanitized shell startup example |
| `tools/linkedin.py` | LinkedIn API helper; credentials stay in macOS Keychain |
| `relink.sh` | Restore active configuration symlinks without overwriting private settings |

## Local setup and sync

The checkout lives at `~/Documents/agent-setup`. GitHub contains audited settings, not a complete backup of credentials or sessions. Pull changes with `git pull --ff-only`, then run `./relink.sh` if links need restoring. Preview with `./relink.sh --dry-run`.

Review the files before using this personal setup: paths, model selections, account-specific integrations, and permissive agent approval settings are intentional choices for my Mac, not universal recommendations. Install the applications separately. Some settings contain my home-directory paths and must be adapted on another Mac.

Live Codex, Cursor CLI, OpenCode provider/MCP, and shell settings that contain credentials or account data are kept at `~/.config/agent-setup-private/`, outside Git and iCloud. Their public counterparts are `*.example.*` (and `shell/zshrc.example`). The relink script preserves existing private settings. On a fresh machine it creates private copies from those examples; configure credentials there or in a secret store. It never copies private values into this repo. Existing files displaced by relinking are backed up under `~/.local/share/agent-setup-relink-backups/`.

Claude MCP registrations live separately in `~/.claude.json`, not in this repository. Browser/CUA skills and the HerdR plugin binaries are installed separately and are not vendored here. Current optional plugin: `kryptamine/herdr-auto-title` v0.13.2. Its config disables pane naming and workspace topics, so only tab titles change. cmux and Copilot are not part of this setup.

## Clipboard images in Ghostty

[ghostty-paste](https://github.com/DonghwanJeong/ghostty-paste) is installed separately at `~/Applications/ghostty-paste.app`, with login startup through `~/Library/LaunchAgents/com.github.ghostty-paste.plist`. The installed build comes from reviewed upstream commit `4a55beb5a65ab1484903b0fa946c5027635704d1` (app version 0.1.1).

Enable its macOS Accessibility permission. When Ghostty is frontmost and the clipboard contains a PNG/TIFF image, it translates Command-V into Control-V; text-only paste is unchanged. The foreground agent must support Control-V image attachment. Claude is documented upstream; Codex/OpenCode inside HerdR still need an end-to-end check. App binaries and permissions are not synced by this repo or `relink.sh`.

## Publishing safely

`.gitignore` is an explicit file allowlist. Auth files, live private configurations, backups, sessions, logs, caches, and third-party plugin directories are excluded. Do not force-add them.

Run `python3 scripts/check-public.py` after staging. It scans the exact staged files with Gitleaks and checks structured configs for literal secrets/account identifiers. Enable the local commit guard with `git config core.hooksPath .githooks` (requires `gitleaks` on PATH). This reduces accidental exposure but cannot guarantee that arbitrary future edits contain no sensitive information.

These instructions guide agent behaviour; they do not enforce runtime security permissions.

## Closing panes

Command-W uses `scripts/herdr-close-pane.py` in HerdR’s built-in terminal popup container. The custom confirmation appears for the final pane or a running agent/command: Enter closes, Escape cancels. After confirmation, closing the final pane creates a fresh tab in the same directory to keep its workspace open. Cancellation, timeout, or a changed foreground process leaves the pane untouched. This is a custom close handler, not HerdR’s stock close dialog.

Explicit workspace closes retain HerdR’s original native confirmation (`ui.confirm_close = true`). Command-Shift-T remains configured to reopen recent closes.

## Reopen closed panes and tabs

Command-Shift-T sends HerdR prefix+u to [herdr-pane-reopen](https://github.com/rchougule/herdr-pane-reopen), installed separately from commit `c8e72c535db5795b878698edeead5b3aa95fbccd` (0.1.1). It remembers recent closes locally and restores layouts and recorded agent conversations; it cannot restore killed processes or unsaved editor state. Claude, Codex, Cursor and OpenCode require their HerdR integrations for session IDs. Install these with `herdr integration install <agent>` on a new machine; restart existing agents if they have not reported their sessions yet. Reopen can start a fresh agent session if resume fails, so check its restore report.

Install using `herdr plugin install rchougule/herdr-pane-reopen --ref c8e72c535db5795b878698edeead5b3aa95fbccd`, then `herdr server reload-config` and `herdr plugin action invoke rchougule.reopen.doctor`. Rust is required to build it. Reload Ghostty configuration with Command-Shift-comma after linking the config. Plugin state and conversation IDs remain local and are not committed.
