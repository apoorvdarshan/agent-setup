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

## Publishing safely

`.gitignore` is an explicit file allowlist. Auth files, live private configurations, backups, sessions, logs, caches, and third-party plugin directories are excluded. Do not force-add them.

Run `python3 scripts/check-public.py` after staging. It scans the exact staged files with Gitleaks and checks structured configs for literal secrets/account identifiers. Enable the local commit guard with `git config core.hooksPath .githooks` (requires `gitleaks` on PATH). This reduces accidental exposure but cannot guarantee that arbitrary future edits contain no sensitive information.

These instructions guide agent behaviour; they do not enforce runtime security permissions.
