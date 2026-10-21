"""Check that reassembling the library preserves all reviewed override bytes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'library/tests').glob('*.json'))}

before = hashes()
subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'scripts/prepare_library.py'), 'assemble'], cwd=ROOT, check=True, capture_output=True)
after = hashes()
changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
equal = all((ROOT/'library/preparation/overrides'/name).read_bytes() == (ROOT/'library/tests'/name).read_bytes() for name in after)
report = {'operation': 'Reassemble all selected books from cached extraction plus final full overrides', 'tests': len(after), 'changedTests': changed, 'allOverrideBytesEqual': equal, 'beforeSha256': before, 'afterSha256': after}
(ROOT/'library/preparation/rebuild-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
assert not changed and equal, 'Rebuild changed reviewed content. Inspect the report.'
print(json.dumps({'tests': len(after), 'changedTests': changed, 'allOverrideBytesEqual': equal}))
