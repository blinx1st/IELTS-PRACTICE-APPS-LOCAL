"""Portable fingerprints: ignore checkout line endings and absolute folder names."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {'.ts', '.tsx', '.css', '.html', '.json', '.py', '.mjs', '.txt'}
INPUTS = ('package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts',
          'scripts/build_state.py', 'scripts/build-state.mjs')


def fingerprint(paths, root):
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(root).as_posix()):
        data = path.read_bytes()
        if path.suffix in TEXT: data = data.replace(b'\r\n', b'\n')
        digest.update(path.relative_to(root).as_posix().encode('utf-8') + b'\0')
        digest.update(data + b'\0')
    return digest.hexdigest()


def build_fingerprint(root=ROOT):
    paths = [p for p in (root/'frontend').rglob('*') if p.is_file() and p.suffix in TEXT | {'.png', '.svg', '.wav', '.ttf'}]
    paths.extend(root/name for name in INPUTS if (root/name).is_file())
    return fingerprint(paths, root)


def build_info(root=ROOT):
    try: return json.loads((root/'dist/build-info.json').read_text(encoding='utf-8'))
    except (OSError, ValueError): return {}


def build_is_current(root=ROOT):
    try:
        dist=root/'dist'
        index=(dist/'index.html').read_text(encoding='utf-8')
        assets=re.findall(r'(?:src|href)="(/assets/[^"?]+)',index)
        return (bool(assets) and all((dist/url.lstrip('/')).is_file() for url in assets) and
                build_info(root).get('sourceFingerprint') == build_fingerprint(root) and
                (dist/'app-logo.png').read_bytes() == (root/'frontend/public/app-logo.png').read_bytes())
    except OSError:return False


def runtime_fingerprint(root=ROOT):
    paths = list((root/'backend').glob('*.py')) + [root/'scripts/build_state.py']
    return hashlib.sha256((fingerprint(paths,root)+build_fingerprint(root)).encode()).hexdigest()
