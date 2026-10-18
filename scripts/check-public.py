#!/usr/bin/env python3
"""Scan exactly the Git index, never live private symlink targets."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
def git(*args):
 return subprocess.check_output(['git', '-C', str(root), *args])

if not shutil.which('gitleaks'):
 raise SystemExit('Install gitleaks before publishing: brew install gitleaks')
secret_keys = {'apikey', 'token', 'accesstoken', 'refreshtoken', 'password', 'secret', 'clientsecret', 'authorization', 'privatekey', 'authid', 'userid'}
def inspect(value, filename):
 if isinstance(value, dict):
  for key, child in value.items():
   normalized = re.sub('[^a-z]', '', key.lower())
   if normalized in secret_keys and isinstance(child, (str, int)) and child:
    if not isinstance(child, str) or not re.fullmatch(r'(?:Bearer )?\{env:[A-Z0-9_]+\}', child):
     raise SystemExit('Literal secret/account field rejected in '+filename+': '+key)
   inspect(child, filename)
 elif isinstance(value, list):
  for child in value: inspect(child, filename)

with tempfile.TemporaryDirectory(prefix='agent-setup-staged-') as temp:
 for entry in git('ls-files', '--stage', '-z').split(b'\0'):
  if not entry: continue
  metadata, raw_path = entry.split(b'\t', 1)
  mode, _, stage = metadata.split()
  name = raw_path.decode()
  if mode == b'120000' or stage != b'0':
   raise SystemExit('Public files must be regular, conflict-free files: '+name)
  data = git('show', ':'+name)
  dest = Path(temp)/name
  dest.parent.mkdir(parents=True, exist_ok=True)
  dest.write_bytes(data)
  if name.endswith(('.json', '.jsonc')):
   inspect(json.loads(data), name)
 subprocess.run(['gitleaks', 'dir', temp, '--redact', '--no-banner', '--log-level', 'error'], check=True)
print('Staged public files passed credential-field checks and Gitleaks.')
