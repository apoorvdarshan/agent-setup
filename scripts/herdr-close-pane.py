#!/usr/bin/env python3
"""Close the shortcut's pane, preserving its workspace with a fresh final tab."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def run(*args):
    result = subprocess.run([os.environ.get('HERDR_BIN_PATH', '/opt/homebrew/bin/herdr'), *args],
                            capture_output=True, text=True, check=True)
    reply = json.loads(result.stdout)
    if 'error' in reply:
        raise RuntimeError(reply['error'].get('message', 'HerdR command failed'))
    return reply['result']


def close(pane_id):
    pane = run('pane', 'get', pane_id)['pane']
    workspace = pane['workspace_id']
    key = hashlib.sha256((os.environ.get('HERDR_SOCKET_PATH', '') + workspace).encode()).hexdigest()
    locks = Path.home() / '.cache/herdr-close-pane'
    locks.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (locks / key).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Re-read after acquiring the lock: repeated shortcuts may target a closed pane.
        pane = run('pane', 'get', pane_id)['pane']
        panes = run('pane', 'list', '--workspace', workspace)['panes']
        if len(panes) == 1 and panes[0]['pane_id'] == pane_id:
            cwd = pane.get('foreground_cwd') or pane['cwd']
            created = run('tab', 'create', '--workspace', workspace, '--cwd', cwd, '--no-focus')
            replacement = created['root_pane']['pane_id']
            live = run('pane', 'list', '--workspace', workspace)['panes']
            if not any(p['pane_id'] == replacement for p in live):
                raise RuntimeError('Replacement pane not confirmed; original pane kept open')
        run('pane', 'close', pane_id)


if __name__ == '__main__':
    # Custom commands report the keypress target explicitly. Never guess from focus.
    pane_id = os.environ.get('HERDR_ACTIVE_PANE_ID')
    if not pane_id:
        sys.exit('Missing HerdR shortcut pane context; nothing closed')
    try:
        close(pane_id)
    except (subprocess.CalledProcessError, ValueError, KeyError, RuntimeError, OSError) as exc:
        sys.exit(f'Pane close stopped: {type(exc).__name__}')
