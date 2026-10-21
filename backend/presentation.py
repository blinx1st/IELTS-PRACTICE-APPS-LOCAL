"""Read-only presentation upgrades for immutable historical content snapshots."""
import copy
import hashlib
import json


def signature(group):
    base = {k: v for k, v in group.items() if k != 'layout'}
    return hashlib.sha256(json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def present(test, library):
    registry = library / 'presentation.json'
    if not registry.is_file():
        return copy.deepcopy(test)
    layouts = json.loads(registry.read_text(encoding='utf-8')).get('groups', {})
    result = copy.deepcopy(test)
    for p in result['passages']:
        for g in p['groups']:
            entry = layouts.get(g['id'])
            if not g.get('layout') and entry and signature(g) == entry['baseSha256']:
                g['layout'] = entry['layout']
    return result


def part_counts(test):
    refs = {}
    for p in test['passages']:
        for g in p['groups']:
            layout = g.get('layout', {})
            if layout.get('kind') != 'table':
                continue
            for row in layout['rows']:
                for cell in row['cells']:
                    for item in cell['content']:
                        if isinstance(item, dict):
                            n = str(item['number'])
                            refs[n] = max(refs.get(n, 0), item.get('part', 0) + 1)
    return {n: count for n, count in refs.items() if count > 1}
