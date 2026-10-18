#!/usr/bin/env python3
"""Link audited settings; preserve live private configs and existing files."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--home', type=Path, default=Path.home(), help='Target home (also useful for isolated verification)')
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()
base = Path(__file__).resolve().parents[1]
home = args.home.expanduser().resolve()
private = home / '.config/agent-setup-private'
backup = home / '.local/share/agent-setup-relink-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
public = {
 '.codex/AGENTS.md': 'AGENTS.md', '.claude/CLAUDE.md': 'AGENTS.md',
 '.config/opencode/AGENTS.md': 'AGENTS.md', '.cursor/rules/apoorv-global.mdc': 'AGENTS.md',
 '.claude/settings.json': 'claude/settings.json', '.cursor/mcp.json': 'cursor/mcp.json',
 '.config/opencode/cli.json': 'opencode/cli.json', '.config/ghostty/config': 'ghostty/config',
 '.config/herdr/config.toml': 'herdr/config.toml', '.config/herdr/color-shell': 'herdr/color-shell',
 '.config/herdr-auto-title/config.env': 'herdr-auto-title/config.env',
}
local = {
 '.codex/config.toml': ('codex/config.toml', 'codex/config.example.toml'),
 '.cursor/cli-config.json': ('cursor/cli-config.json', 'cursor/cli-config.example.json'),
 '.config/opencode/opencode.json': ('opencode/opencode.json', 'opencode/opencode.example.json'),
 '.config/opencode/opencode.jsonc': ('opencode/opencode.jsonc', 'opencode/opencode.example.jsonc'),
 '.zshrc': ('shell/zshrc', 'shell/zshrc.example'),
}

def link(dest, target):
 if dest.is_symlink() and dest.resolve() == target.resolve():
  return
 if args.dry_run:
  print('Would link:', dest, '->', target)
  return
 if dest.exists() or dest.is_symlink():
  saved = backup / dest.relative_to(home)
  saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
  shutil.move(str(dest), str(saved))
 dest.parent.mkdir(parents=True, exist_ok=True)
 dest.symlink_to(target)
 print('Linked:', dest)

for rel, (runtime, template) in local.items():
 dest, target = home / rel, private / runtime
 if not target.exists() and not args.dry_run:
  target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
  if dest.exists():
   shutil.copy2(dest.resolve(), target)
  else:
   text = (base / template).read_text().replace('/Users/apoorvdarshan', str(home))
   target.write_text(text)
  target.chmod(0o600)
 link(dest, target)
for rel, source in public.items():
 link(home / rel, base / source)
print('Done. Private settings are preserved; secrets are never copied into the repository.')
