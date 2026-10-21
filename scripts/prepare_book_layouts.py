"""Source-based document presentation; preserves original text anchors and snapshots.

Run after the Reading/Listening importers. --check verifies without writing.
Only optional layout metadata is changed. Every visible text fragment retains its
original annotation anchor and offset, including fragments split into subheadings.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.presentation import signature, layout_signature

LIB = ROOT / 'library'
# Ratios measured against the Source images. Cambridge 20's retyped, unruled
# tables need a slightly wider name column to avoid the source's broken words.
TABLES = {
    'cam13-t1-p1-g1': ([27, 73], 'grid'),
    'cam13-t3-p1-g1': ([13, 32, 55], 'grid'),
    'cam15-t1-p1-g3': ([23, 77], 'grid'),
    'cam15-t4-p1-g2': ([53, 47], 'grid'),
    'cam16-t1-p1-g2': ([100], 'boxed-notes'),
    'cam17-t4-p1-g2': ([26, 74], 'grid'),
    'cam18-t1-p1-g2': ([21, 27, 26, 26], 'grid'),
    'l-cam13-t1-p1-g1': ([27, 32, 41], 'grid'),
    'l-cam15-t1-p2-g15': ([10, 45, 45], 'grid'),
    'l-cam15-t2-p1-g1': ([21, 34, 45], 'grid'),
    'l-cam17-t2-p1-q8-10': ([10, 30, 19, 41], 'grid'),
    'l-cam18-t2-p1-q6-10': ([24, 25, 23, 28], 'grid'),
    'l-cam18-t3-p1-q5-10': ([34, 28, 38], 'grid'),
    'l-cam19-t2-p1-q7-10': ([18, 45, 37], 'grid'),
    'l-cam19-t3-p1-q7-10': ([22, 39, 39], 'grid'),
    'l-cam19-t4-p1-q7-10': ([22, 25, 27, 26], 'grid'),
    'l-cam20-t1-p1-q1-10': ([16, 21, 31, 32], 'plain'),
    'l-cam20-t3-p1-q1-10': ([22, 34, 44], 'plain'),
}
MARKER = re.compile(r'^(\s*)([\u2022\u25cf\uf0b7]|[\u2013\u2014-]|[\u25cb\u25e6]|o(?=\s))\s*')
# Source-reviewed lists in older transcriptions used plain <p> blocks. Indexes
# refer to the ORIGINAL blocks, so their annotation identities remain stable.
BULLETS = {
    'l-cam13-t1-p4-g31': [3,4,7,10,12,14],
    'l-cam13-t2-p1-g1': [3,4,5,6,8,9,10,14,15,16,17,18],
    'l-cam13-t2-p4-g31': [1,2,5,6,7,9,10,11,13,15,16,17,18],
    'l-cam13-t3-p1-g1': [3,5,6,7,8,10,11,12,14,15],
    'l-cam13-t3-p4-g31': [2,3,4,5,6,8,10,11],
    'l-cam13-t4-p1-g1': [3,4,5,6,8,9,10,11,12,14,15,16],
    'l-cam13-t4-p4-g31': [2,3,4,6,7,9,10,11,12,13,14,16,17],
    'l-cam14-t1-p4-g31': [4,5,11,12,16,17,18,19,21,22,23,24],
    'l-cam14-t2-p4-g31': [2,3,4,5,6,8,9,10,12,13,15,16,17,18,19,20],
    'l-cam14-t3-p1-g1': 'body',
    'l-cam14-t3-p4-g31': 'body',
    'l-cam14-t4-p4-g31': 'body',
    'l-cam15-t1-p1-g1': 'body',
    'l-cam15-t1-p4-g31': 'body',
    'l-cam15-t2-p1-g5': 'body',
    'l-cam15-t2-p4-g31': 'body',
    'l-cam15-t3-p1-g1': [4,5,6,7,9,10,11,13,17,18,20,21,22,23,24,25,27,28,29],
    'l-cam15-t3-p3-g21': 'body',
    'l-cam15-t3-p4-g31': 'body',
    'l-cam15-t4-p4-g31': [2,3,6,7,8,10,11,15,16,19],
    'l-cam16-t1-p1-g1': [3,4,5,8,9,10,11],
    'l-cam16-t1-p4-g31': [3,4,6,7,8,9,11,12,13,14,15,18,20,21],
    'l-cam16-t2-p1-g1': [3,4,6,7,9,10,11,13,14,16,17],
    'l-cam16-t2-p4-g31': [2,3,4,5,7,8,9,10,11,12,13,15,16],
    'l-cam16-t3-p1-g1': [2,3,5,6,8,9,10,12,13,14,15,17,18,19,21],
    'l-cam16-t3-p4-g31': 'body',
    'l-cam16-t4-p1-g1': [3,4,6,7,8,9,10,11,12,13,15,16],
    'l-cam16-t4-p4-g31': [3,4,5,6,8,9,10,11,12,13,14,16,17,18,19],
}
NESTED = {
    'l-cam17-t1-p4-q31-40': [5,6,8,19,20],
    'l-cam17-t3-p1-q1-10': [6,7,9,10,11,17,18],
    'l-cam17-t3-p4-q31-40': [7,8,13,15,16],
    'l-cam17-t4-p1-q1-10': [7,8,10,11],
    'l-cam18-t1-p4-q31-40': [11,12,13,14,15],
    'l-cam19-t1-p4-q31-40': [5,6,11,12],
    'l-cam19-t3-p4-q31-40': [15,16,17,19,20],
    'l-cam19-t4-p4-q31-40': [13,14,18,19,20],
    'l-cam20-t1-p4-q31-40': [5,6,12,13],
}


def flatten(block, anchor):
    text = ''; spans = []
    for i, token in enumerate(block['content']):
        value = token if isinstance(token, str) else '\ufffc'
        anchors = block.get('anchors', [])
        offsets = block.get('offsets', [])
        spans.append((len(text), len(text)+len(value), token,
                      anchors[i] if i < len(anchors) and anchors[i] else f'{anchor}-{i}',
                      offsets[i] if i < len(offsets) else 0))
        text += value
    return text, spans


def fragment(spans, start, end):
    content = []; anchors = []; offsets = []
    for lo, hi, token, anchor, offset in spans:
        a, b = max(start, lo), min(end, hi)
        if a >= b:
            continue
        content.append(token[a-lo:b-lo] if isinstance(token, str) else token)
        anchors.append(anchor if isinstance(token, str) else '')
        offsets.append(offset+a-lo if isinstance(token, str) else 0)
    return {'content': content, 'anchors': anchors, 'offsets': offsets}


def blocks_for(old, anchor, *, variant='notes', title=False, table=False):
    text, spans = flatten(old, anchor)
    lines = list(re.finditer(r'[^\n]+(?:\n|$)|\n', text))
    breaks = {0, len(text)}; roles = {}; markers = {}
    first_text = True
    for index, line in enumerate(lines):
        raw = line[0].rstrip('\n'); stripped = raw.strip()
        if not stripped:
            breaks.update((line.start(), line.end()))
            continue
        marker = MARKER.match(raw)
        # A printed number at the start of a sentence is already displayed beside
        # its input. Remove the duplicate label, not the question's text/anchor.
        numbered = re.match(r'^\s*(\d{1,2})\s+', raw) if variant == 'sentences' else None
        if marker:
            breaks.add(line.start())
            symbol = marker[2]
            kind = 'dash' if symbol in '\u2013\u2014-' else 'circle' if symbol in '\u25cb\u25e6o' else 'bullet'
            depth = 2 if kind == 'circle' else 1 if kind == 'dash' else 0
            markers[line.start()] = (marker.end(), kind, depth)
        elif numbered:
            breaks.add(line.start()); roles[line.start()] = ('body', numbered.end())
        elif first_text and (old['tag'] == 'h3' or title and len(stripped) < 100 and '\ufffc' not in raw and not stripped.endswith(('.', ':')) and not (index+1<len(lines) and re.match(r'^[a-z]',lines[index+1][0].strip()))):
            breaks.update((line.start(), line.end())); roles[line.start()] = ('title' if title else 'section', 0)
        elif old['tag'] == 'h3':
            breaks.update((line.start(), line.end())); roles[line.start()] = ('section', 0)
        elif stripped == 'Assessment of mother’s needs':
            breaks.update((line.start(),line.end()));roles[line.start()]=('section',0)
        elif (variant != 'summary' and not table and old['tag']!='li' and '\ufffc' not in raw and not (index and MARKER.fullmatch(lines[index-1][0].strip())) and
              ((stripped.endswith(':') and len(stripped) < 85) or
               ((stripped[0].isupper() or re.match(r'^\d{4}s?(?:,|$)',stripped)) and len(stripped) < 78 and not re.search(r'[.;!?]$', stripped) and
                index+1 < len(lines) and (not lines[index+1][0].strip() or MARKER.match(lines[index+1][0]) or (first_text and title))))):
            breaks.update((line.start(), line.end())); roles[line.start()] = ('label' if stripped.endswith(':') else 'section', 0)
        first_text = False
    result = []; boundaries = sorted(breaks)
    for start, end in zip(boundaries, boundaries[1:]):
        role, skip = roles.get(start, ('body', 0))
        marker = markers.get(start)
        if marker:
            skip = marker[0]
        start_text = start+skip
        while start_text < end and text[start_text].isspace(): start_text += 1
        while end > start_text and text[end-1].isspace(): end -= 1
        if start_text == end:
            # Standalone PDF bullet glyph is attached to the following text block.
            if marker and end < len(text): markers[boundaries[boundaries.index(start)+1]] = (0, marker[1], marker[2])
            continue
        # A bullet glyph on its own line belongs to the whole following item.
        value = fragment(spans, start_text, end)
        tag = 'h3' if role in ('title', 'section') else 'li' if marker or old['tag']=='li' else 'p'
        value.update(tag=tag, role=role)
        if marker: value.update(marker=marker[1], depth=marker[2])
        elif old['tag']=='li': value.update(marker='bullet', depth=0)
        result.append(value)
    return result


def flow_variant(group):
    ins = group['instructions'].lower()
    if 'summary' in ins: return 'summary'
    if 'sentence' in ins: return 'sentences'
    if 'form' in ins: return 'form'
    return 'notes'


def upgrade(group):
    old = group['layout']
    if old.get('presentationVersion') == 3: return old
    layout = copy.deepcopy(old)
    layout['presentationVersion'] = 3
    if layout['kind'] == 'flow':
        variant = flow_variant(group); layout['variant'] = variant
        if group['id'].startswith('l-'):
            layout['frame']='none' if group['id'].startswith('l-cam20-') else 'box'
        else:
            book=int(re.search(r'cam(\d+)',group['id'])[1])
            layout['frame']='none' if variant=='sentences' or book==13 or variant=='summary' and (book in (14,15) or book==16 and not group['id'].startswith('cam16-t3-')) else 'box'
        layout['optionsPosition'] = 'after' if group.get('options') else 'before'
        blocks=[]
        for i, block in enumerate(old['blocks']):
            parsed=blocks_for(block, f"{group['id']}-flow-{i}", variant=variant, title=i==0 and variant!='sentences')
            bullet_indexes=BULLETS.get(group['id'],[])
            for b in parsed:
                if b['role']=='body' and not b.get('marker') and not str(b['content'][0]).startswith('Example:') and (bullet_indexes=='body' or i in bullet_indexes):
                    b.update(marker='bullet',depth=0,tag='li')
                if i in NESTED.get(group['id'],[]): b.update(marker='dash',depth=1,tag='li',role='body')
                if group['id']=='l-cam13-t3-p4-g31' and i in (16,17,18,19): b['depth']=0
                # A form's labels share a column, with the answer kept in its
                # original sentence on the right. Do not split section headings.
                if variant=='form' and b['role']=='body' and not b.get('marker') and isinstance(b['content'][0],str):
                    first=b['content'][0]; label=re.match(r'^.{1,55}?:\s*',first)
                    if label and (label.end()<len(first) or len(b['content'])>1): b['labelEnd']=label.end()
            blocks.extend(parsed)
        layout['blocks'] = blocks
        if group['id'].startswith('l-cam20-') or group['id']=='l-cam13-t2-p4-g31':
            for b in blocks:
                if b['role']=='title': b['align']='left'
        if group['id']=='l-cam20-t2-p1-q1-10':
            # Its source starts with a two-line lead-in, not a separate title.
            blocks[0]['role']='body';blocks[0]['tag']='p'
            for b in blocks:
                text=''.join(t for t in b['content'] if isinstance(t,str)).strip()
                if text=='Assessment of mother’s needs': b.update(role='section',tag='h3')
        if group['id']=='cam17-t2-p1-g1':
            for b in blocks:
                if b['content']==['Discovery']: b.update(role='section',tag='h3')
                if b['content']==['Qumran, 1946/7']: b.update(role='body',tag='p')
        if group['id']=='cam18-t2-p1-g1':
            for b in blocks:
                if re.fullmatch(r'Stage \d:', ''.join(t for t in b['content'] if isinstance(t,str))): b.update(role='body',tag='p')
    else:
        widths, variant = TABLES[group['id']]
        layout.update(columnWidths=widths, variant=variant)
        if group['id']=='cam15-t4-p1-g2': layout['answerWidths']={'7':10}
        occupied = {}; minimum = 36
        for ri, row in enumerate(layout['rows']):
            column = 0
            for ci, cell in enumerate(row['cells']):
                while (ri, column) in occupied: column += 1
                rs, cs = cell.get('rowSpan',1), cell.get('colSpan',1)
                for r in range(ri,ri+rs):
                    for c in range(column,column+cs): occupied[r,c] = True
                cell['blocks'] = blocks_for({'tag':'p','content':cell['content']}, f"{group['id']}-cell-{ri}-{ci}", title=False, table=True)
                if group['id']=='l-cam19-t4-p1-q7-10' and ri>0 and column==0: cell['header']=True
                if cell.get('header'): cell['scope']='row' if column==0 and ri>0 and cs==1 else 'col'
                if any(isinstance(t,dict) for t in cell['content']):
                    field = {1:12,2:16,3:20}.get(group.get('wordLimit'),16)
                    if group['id']=='cam15-t4-p1-g2': field=28  # two 10ch fields, the printed 'and'
                    fraction = sum(widths[column:column+cs])/100
                    minimum = max(minimum, math.ceil((field+8)/fraction))
                column += cs
        layout['minWidthCh'] = minimum
    return layout


def refs(layout):
    if layout['kind']=='flow': return [t for b in layout['blocks'] for t in b['content'] if isinstance(t,dict)]
    return [t for r in layout['rows'] for c in r['cells'] for b in c.get('blocks',[{'content':c['content']}]) for t in b['content'] if isinstance(t,dict)]


def validate(group, old, new):
    assert refs(old)==refs(new), (group['id'], 'answer order changed')
    originals = {}
    if old['kind']=='flow':
        sources = [(b, f"{group['id']}-flow-{i}") for i,b in enumerate(old['blocks'])]
    else:
        sources = [({'content':c['content']},f"{group['id']}-cell-{ri}-{ci}") for ri,r in enumerate(old['rows']) for ci,c in enumerate(r['cells'])]
    for block, anchor in sources:
        _, spans = flatten(block, anchor)
        for _,_,token,identity,offset in spans:
            if isinstance(token,str): originals.setdefault(identity,[]).append((offset,token))
    blocks = new['blocks'] if new['kind']=='flow' else [b for r in new['rows'] for c in r['cells'] for b in c['blocks']]
    for block in blocks:
        for i, token in enumerate(block['content']):
            if not isinstance(token,str): continue
            identity, offset = block['anchors'][i], block['offsets'][i]
            assert any(token == text[offset-base:offset-base+len(token)] for base,text in originals.get(identity,[]) if offset>=base), (group['id'], identity, offset)
    if new['kind']=='table': assert sum(new['columnWidths'])==100


def text_digest(layout, variant):
    """Ignore PDF wrapping/markers and duplicate sentence numbers, never words."""
    if layout['kind']=='flow': blocks=layout['blocks']
    else: blocks=[b for r in layout['rows'] for c in r['cells'] for b in c.get('blocks',[{'content':c['content']}])]
    text=[]
    for b in blocks:
        s=''.join(t if isinstance(t,str) else '\ufffc' for t in b['content'])
        s=re.sub(r'(?m)^\s*[\u2022\u25cf\uf0b7\u2013\u2014\u25cb\u25e6-]\s*','',s)
        s=re.sub(r'(?m)^\s*o\s+','',s)
        if variant=='sentences':s=re.sub(r'(?m)^\s*\d{1,2}\s+','',s)
        text.append(s)
    import hashlib
    return hashlib.sha256(re.sub(r'\s+',' ',' '.join(text)).strip().encode('utf-8')).hexdigest()


def write(path, value, check):
    if check: assert json.loads(path.read_text(encoding='utf-8'))==value, f'Out of date: {path}'
    else: path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    registry=json.loads((LIB/'presentation.json').read_text(encoding='utf-8'))
    report=[]
    for directory, overrides in [('tests','preparation/overrides'),('listening/tests','preparation/listening/overrides/tests')]:
        for path in sorted((LIB/directory).glob('*.json')):
            test=json.loads(path.read_text(encoding='utf-8')); changed=False
            for p in test.get('parts',test.get('passages',[])):
                for group in p['groups']:
                    old=group.get('layout',{})
                    if old.get('kind') not in ('flow','table'): continue
                    layout=upgrade(group); validate(group,old,layout)
                    digest=text_digest(old,layout.get('variant'))
                    assert digest==text_digest(layout,layout.get('variant')),(group['id'],'visible text changed')
                    previous=registry['groups'].get(group['id'],{})
                    hashes=set(previous.get('previousLayoutSha256',[]))
                    if old!=layout: hashes.add(layout_signature(old))
                    if previous.get('baseSha256')==signature(group) and previous.get('layout')!=layout:
                        hashes.add(layout_signature(previous['layout']))
                    registry['groups'][group['id']]={'baseSha256':signature(group),'previousLayoutSha256':sorted(hashes),'layout':layout}
                    group['layout']=layout; changed=True
                    report.append({'groupId':group['id'],'kind':layout['kind'],'questions':[q['number'] for q in group['questions']],'sourceImages':group.get('sourceImages',[]),'baseSha256':signature(group),'layoutSha256':layout_signature(layout),'visibleTextSha256':digest,'anchorCheck':'exact original text slices'})
            if changed:
                write(path,test,args.check);write(LIB/overrides/path.name,test,args.check)
    assert sum(g['kind']=='table' for g in report)==18
    assert sum(g['kind']=='flow' for g in report)==146
    write(LIB/'presentation.json',registry,args.check)
    write(LIB/'preparation/book-layout-review.json',{'schemaVersion':3,'date':'2026-10-22','tables':18,'flows':146,'groups':report,'errors':[]},args.check)
    print(json.dumps({'tables':18,'flows':146,'errors':0,'check':args.check}))


if __name__=='__main__':main()
