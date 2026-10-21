"""Reproducible, source-reviewed Reading completion layouts. --check never writes."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from backend.presentation import signature
LIB = ROOT / 'library'
BLANK = re.compile(r'\b(\d{1,2})\s*(?:_{3,}|[.\u2026\u00b7]{3,})')
PLACEHOLDER = re.compile(r'\{\{(\d+)\}\}')

def tokens(text):
    result=[];start=0
    for m in PLACEHOLDER.finditer(text):
        result.extend([text[start:m.start()], {'number':int(m[1])}]);start=m.end()
    result.append(text[start:]);return result

def eligible(g):
    return (g['type']=='completion' and 'diagram' not in g['instructions'].lower() or
            g['type']=='matching' and 'summary' in g['instructions'].lower()) and g.get('layout',{}).get('kind') not in ('table','matrix','diagram')

def layout_for(g,reviewed):
    nums=[q['number'] for q in g['questions']]
    if g['id'] in reviewed:
        blocks=[]
        for line in reviewed[g['id']].splitlines():
            if not line.strip():continue
            tag='h3' if line.startswith('# ') else 'li' if line.startswith('\u2022 ') else 'p'
            blocks.append({'tag':tag,'content':tokens(line[2:] if tag in ('h3','li') else line)})
        return {'kind':'flow','blocks':blocks}
    body=g.get('body','')
    # Existing word-bank lists are rendered once beside the inline paragraph.
    if g.get('options'):
        body=re.split(r'\n\s*A\.\s',body,maxsplit=1)[0].rstrip()
    matches=[m for m in BLANK.finditer(body) if int(m[1]) in nums]
    if [int(m[1]) for m in matches]==nums:
        content=[];anchors=[];offsets=[];start=0
        old_inline=g['type']=='completion' and g.get('renderMode')!='source'
        for m in matches:
            content.extend([body[start:m.start()],{'number':int(m[1])}])
            anchors.extend([g['id']+'-body-'+str(start) if old_inline else g['id']+'-body',''])
            offsets.extend([0 if old_inline else start,0]);start=m.end()
        content.append(body[start:]);anchors.append(g['id']+'-body-end' if old_inline else g['id']+'-body');offsets.append(0 if old_inline else start)
        return {'kind':'flow','blocks':[{'tag':'p','content':content,'anchors':anchors,'offsets':offsets}]}
    # Sentence completions put the question number at the start of the sentence,
    # rather than beside its blank. Use the reviewed individual question text.
    blocks=[]
    for q in g['questions']:
        text=q['text'].strip()
        if not text:
            match=re.search(r'(?ms)^\s*'+str(q['number'])+r'\s+(.+?)(?=^\s*(?:'+('|'.join(map(str,nums)))+r')\s+|\Z)',body)
            if match:text=match[1].strip()
        text=re.sub(r'^'+str(q['number'])+r'\s+','',text)
        blanks=list(re.finditer(r'_{3,}|[.\u2026\u00b7]{3,}',text))
        if len(blanks)!=1:raise ValueError(f"Needs source transcription: {g['id']} Q{q['number']}")
        m=blanks[0];blocks.append({'tag':'p','content':[text[:m.start()],{'number':q['number']},text[m.end():]]})
    return {'kind':'flow','blocks':blocks}

def validate(g,layout):
    refs=[v['number'] for b in layout['blocks'] for v in b['content'] if isinstance(v,dict)]
    expected=[q['number'] for q in g['questions']]
    assert refs==expected,(g['id'],refs,expected)
    assert all(isinstance(v,str) or set(v)=={'number'} for b in layout['blocks'] for v in b['content'])
    return refs

def write(path,value,check):
    if check:assert json.loads(path.read_text(encoding='utf-8'))==value,f'Out of date: {path}'
    else:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    reviewed=json.loads((LIB/'preparation/reading-inline-texts.json').read_text(encoding='utf-8'))
    registry=json.loads((LIB/'presentation.json').read_text(encoding='utf-8'));report=[];outputs=[]
    for path in sorted((LIB/'tests').glob('*.json')):
        test=json.loads(path.read_text(encoding='utf-8'));changed=False
        for passage in test['passages']:
            for g in passage['groups']:
                if not eligible(g):continue
                layout=layout_for(g,reviewed);refs=validate(g,layout)
                entry={'baseSha256':signature(g),'layout':layout};g['layout']=layout
                registry['groups'][g['id']]=entry;changed=True
                report.append({'groupId':g['id'],'questions':refs,'sourceImages':g.get('sourceImages',[]),'method':'visual transcription' if g['id'] in reviewed else 'previously reviewed text','baseSha256':entry['baseSha256'],'layoutSha256':hashlib.sha256(json.dumps(layout,sort_keys=True,ensure_ascii=False).encode()).hexdigest()})
        if changed:
            if '.inline2' not in test['version']:test['version']+='.inline2'
            outputs.extend([(path,test),(LIB/'preparation/overrides'/path.name,test)])
    assert len(report)==82,len(report)
    assert len(reviewed)==39,len(reviewed)
    for path,value in outputs:write(path,value,args.check)
    write(LIB/'presentation.json',registry,args.check)
    write(LIB/'preparation/reading-inline-review.json',{'schemaVersion':1,'date':'2026-10-22','groups':report,'totalGroups':82,'sourceTranscriptions':39,'existingReviewedText':43,'errors':[]},args.check)
    print(json.dumps({'groups':len(report),'questions':sum(len(g['questions']) for g in report),'errors':0,'check':args.check}))

if __name__=='__main__':main()
