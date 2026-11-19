"""Refresh tracked source hashes while preserving unavailable firmware hashes."""
from pathlib import Path
import argparse
import json
import subprocess

from verify_files import FIRMWARE_INPUTS, digest

ROOT = Path(__file__).resolve().parent.parent


def update(check=False):
    path = ROOT / 'SHA256SUMS.json'
    previous = json.loads(path.read_text(encoding='utf-8'))
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    manifest = {}
    tracked = (set(names) | FIRMWARE_INPUTS) - {'', 'SHA256SUMS.json'}
    ordered = [name for name in previous if name in tracked]
    ordered += sorted(tracked - previous.keys(), key=str.casefold)
    for name in ordered:
        if not name or name == 'SHA256SUMS.json':
            continue
        file = ROOT / name
        if file.is_file():
            manifest[name] = digest(file)
        elif name in FIRMWARE_INPUTS and name in previous:
            manifest[name] = previous[name]
        else:
            raise FileNotFoundError('Missing tracked file: ' + name)
    if check:
        if manifest != previous:
            raise ValueError('SHA256SUMS.json is stale; run python tools/update_manifest.py')
        print('PASS: manifest covers all tracked files; absent firmware hashes retained')
    else:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\r\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    update(parser.parse_args().check)
