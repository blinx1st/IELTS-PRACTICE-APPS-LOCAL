import copy
import json
from pathlib import Path

from backend.presentation import present, signature, layout_signature
from scripts.prepare_book_layouts import blocks_for, upgrade, refs, validate


def test_layout_upgrade_requires_both_content_and_reviewed_previous_layout(tmp_path):
    old = {'id': 'g', 'body': 'Reviewed text', 'layout': {'kind': 'flow', 'blocks': []}}
    new = {**old['layout'], 'presentationVersion': 3, 'variant': 'notes'}
    test = {'passages': [{'groups': [old]}]}
    untouched = copy.deepcopy(test)
    (tmp_path/'presentation.json').write_text(json.dumps({'groups': {'g': {
        'baseSha256': signature(old), 'previousLayoutSha256': [layout_signature(old['layout'])], 'layout': new,
    }}}), encoding='utf-8')
    assert present(test, tmp_path)['passages'][0]['groups'][0]['layout'] == new
    assert test == untouched
    old['layout']['custom'] = True
    assert present(test, tmp_path) == test
    old['layout'].pop('custom'); old['body'] = 'Different text'
    assert present(test, tmp_path) == test


def test_splitting_pdf_lines_preserves_source_annotation_offsets():
    original = {'tag': 'p', 'content': ['Manatees\n\nAppearance\n\n• look similar to ', {'number': 1}, '\n• can swim\nunder water'],
                'anchors': ['old-body', '', 'old-body'], 'offsets': [0, 0, 93]}
    blocks = blocks_for(original, 'unused', title=True)
    assert [b['role'] for b in blocks[:2]] == ['title', 'section']
    body = blocks[2]
    assert body['anchors'][0] == 'old-body'
    assert body['offsets'][0] == original['content'][0].index('look similar')
    assert blocks[3]['content'] == ['can swim\nunder water']
    assert blocks[3]['offsets'][0] == 93 + original['content'][2].index('can swim')


def test_source_structures_and_answer_coverage_are_reproducible():
    lib = Path(__file__).resolve().parents[1]/'library'
    registry = json.loads((lib/'presentation.json').read_text(encoding='utf-8'))['groups']
    counts = {'table': 0, 'flow': 0}
    for directory in ('tests', 'listening/tests'):
        for path in (lib/directory).glob('*.json'):
            test = json.loads(path.read_text(encoding='utf-8'))
            for unit in test.get('parts', test.get('passages', [])):
                for group in unit['groups']:
                    layout = group.get('layout', {})
                    if layout.get('kind') not in counts: continue
                    counts[layout['kind']] += 1
                    assert layout.get('presentationVersion') == 3
                    assert upgrade(group) == layout
                    validate(group, layout, layout)
                    assert {t['number'] for t in refs(layout)} == {q['number'] for q in group['questions']}
                    assert registry[group['id']]['baseSha256'] == signature(group)
                    assert registry[group['id']]['layout'] == layout
    assert counts == {'table': 18, 'flow': 146}
