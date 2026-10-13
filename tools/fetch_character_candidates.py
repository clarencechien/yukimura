"""Fetch pinned, licensed study assets; never replace the game's models.

Raw sources are cached under .tmp. Hashes and licenses accompany the study.
Run with Python 3, no third-party dependencies.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.tmp/character-candidates'
REPORT = ROOT / 'assets/research/character-candidates'
SOURCES = [
    ('rocketbox', 'microsoft/Microsoft-Rocketbox',
     '0943055db6ec570bcef9f2c8b41c9e5467c808f9',
     'Assets/Avatars/Adults/Male_Adult_10/', 'MIT'),
    ('cyber-samurai', 'Tresjs/assets',
     '2e771aed0124c3af8fb2449a4c59b4ad08d0cc5f',
     'models/gltf/cyber-samurai/', 'CC-BY-4.0'),
]


def read(url):
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    results = []
    for name, repo, commit, prefix, license_id in SOURCES:
        tree = json.loads(read(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1'))
        files = [t for t in tree['tree'] if t['type'] == 'blob' and
                 (t['path'].startswith(prefix) or (name == 'rocketbox' and t['path'] == 'LICENSE.md'))]

        def fetch(t):
            relative = t['path'].removeprefix(prefix)
            dest = OUT / name / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            url = f'https://raw.githubusercontent.com/{repo}/{commit}/{t["path"]}'
            if not dest.exists() or dest.stat().st_size != t['size']:
                dest.write_bytes(read(url))
            data = dest.read_bytes()
            # Git's blob hash validates cache contents against the pinned tree.
            git_hash = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
            if git_hash != t['sha']:
                raise ValueError(f'Hash mismatch: {dest}')
            return {'path': relative, 'source': url, 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest()}

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            downloaded = list(pool.map(fetch, files))
        license_file = 'LICENSE.md' if name == 'rocketbox' else 'license.txt'
        (REPORT / f'{name}-LICENSE.txt').write_bytes((OUT / name / license_file).read_bytes())
        results.append({'id': name, 'repository': repo, 'commit': commit,
                        'license': license_id, 'files': downloaded})
        print(name, len(downloaded), 'files verified', flush=True)
    (REPORT / 'sources.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
