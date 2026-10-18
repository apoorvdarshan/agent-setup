#!/usr/bin/env python3
"""Close the shortcut's pane, preserving its workspace with a fresh final tab."""
import curses
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def run(*args):
    result = subprocess.run([os.environ.get('HERDR_BIN_PATH', '/opt/homebrew/bin/herdr'), *args],
                            capture_output=True, text=True, check=True)
    reply = json.loads(result.stdout)
    if 'error' in reply:
        raise RuntimeError(reply['error'].get('message', 'HerdR command failed'))
    return reply['result']


def process_state(pane):
    info = run('pane', 'process-info', '--pane', pane['pane_id'])['process_info']
    shell = info.get('shell_pid')
    processes = info.get('foreground_processes', [])
    busy = bool(pane.get('agent')) or not shell or not processes or any(
        p.get('pid') != shell for p in processes)
    identity = (pane.get('agent'), info.get('foreground_process_group_id'),
                tuple(sorted(p['pid'] for p in processes)))
    return busy, identity


def confirm_close():
    """Use HerdR's terminal popup; never steal input from the agent's PTY."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return False

    def dialog(screen):
        curses.curs_set(0)
        screen.keypad(True)
        screen.timeout(200)
        curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            screen.erase()
            height, width = screen.getmaxyx()
            lines = ["Close this pane?", "Running processes will stop.",
                     "The workspace stays open.", "", "[ Enter: close ]  [ Esc: cancel ]"]
            for y, text in enumerate(lines):
                if y < height - 1 and width > 1:
                    screen.addnstr(y, 1, text, width - 2,
                                   curses.A_BOLD if y == 0 else curses.A_NORMAL)
            screen.refresh()
            key = screen.getch()
            if key in (10, 13, curses.KEY_ENTER):
                return True
            if key in (27, 3, ord('q'), ord('n')):
                return False
            if key == curses.KEY_MOUSE:
                try:
                    _, x, y, _, buttons = curses.getmouse()
                    if buttons & (curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED) and y == 4:
                        if 1 <= x < 17:
                            return True
                        if 19 <= x < 34:
                            return False
                except curses.error:
                    pass
        return False

    try:
        return curses.wrapper(dialog)
    except (curses.error, KeyboardInterrupt):
        return False


def close(pane_id):
    pane = run('pane', 'get', pane_id)['pane']
    workspace = pane['workspace_id']
    key = hashlib.sha256((os.environ.get('HERDR_SOCKET_PATH', '') + workspace).encode()).hexdigest()
    locks = Path.home() / '.cache/herdr-close-pane'
    locks.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (locks / key).open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return  # A close/confirmation is already in progress for this workspace.
        # Re-read after acquiring the lock: repeated shortcuts may target a closed pane.
        pane = run('pane', 'get', pane_id)['pane']
        busy, identity = process_state(pane)
        initial_panes = run('pane', 'list', '--workspace', workspace)['panes']
        if (busy or len(initial_panes) == 1) and not confirm_close():
            return
        # Never apply an earlier confirmation to a different foreground process.
        pane = run('pane', 'get', pane_id)['pane']
        if process_state(pane)[1] != identity:
            return
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
