"""Structural, asset and scoring checks; editorial evidence remains separate and local."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));LIB=ROOT/'library'
from backend.scoring import grade

def load(p):return json.loads(p.read_text(encoding='utf8'))
def refs(v,key):
    if isinstance(v,dict):
        if key in v:yield v[key]
        for x in v.values():yield from refs(x,key)
    elif isinstance(v,list):
        for x in v:yield from refs(x,key)

def audit():
    issues=[];records=[];hashes={};kinds=Counter();layout_counts=Counter()
    def check(ok,where,problem):
        if not ok:issues.append({'at':where,'problem':problem})
    for b in range(13,21):
        for tn in range(1,5):
            ident=f'cam{b}-listening-test{tn}';path=LIB/'listening/tests'/f'{ident}.json'
            if not path.exists():issues.append({'at':ident,'problem':'Missing test'});continue
            t=load(path);key=load(LIB/'listening/keys'/path.name);script=load(LIB/'listening/transcripts'/path.name)
            check(t.get('verification',{}).get('status')=='verified',ident,'Editorial review incomplete')
            check('answers' not in t and 'transcript' not in t,ident,'Private fields in public test')
            check([p['number'] for p in t['parts']]==[1,2,3,4],ident,'Part order')
            numbers=[]
            for p in t['parts']:
                where=f'{ident}/part{p["number"]}';pn=[];a=p['audio'];asset=LIB/'audio'/Path(a['url']).name
                check(asset.exists(),where,'Missing audio')
                if asset.exists():
                    actual=hashes.setdefault(asset.name,hashlib.sha256(asset.read_bytes()).hexdigest())
                    check(actual==a['sha256'],where,'Audio checksum')
                check(0<=a.get('start',0)<a.get('end',a['duration'])<=a['duration']+.1,where,'Audio boundary')
                check(a.get('verification',{}).get('status')=='verified',where,'Audio content not verified')
                proof=a.get('verification',{}).get('proof');check(bool(proof) and (LIB/proof).exists(),where,'Missing audio evidence')
                check(len(script.get('parts',{}).get(str(p['number']),''))>100,where,'Missing transcript')
                for g in p['groups']:
                    nums=[q['number'] for q in g['questions']];pn+=nums;kinds[g['type']]+=1
                    check(bool(g.get('heading')) and bool(g.get('instructions')),g['id'],'Missing heading/instructions')
                    check(isinstance(g.get('wordLimit',1),int),g['id'],'Word limit type')
                    layout=g.get('layout');layout_counts[layout['kind'] if layout else 'standard']+=1
                    if g['type'] in ('completion','short'):
                        check(bool(layout),g['id'],'Completion has no inline layout')
                    if layout:
                        positioned=list(refs(layout,'number'))
                        check(sorted(set(positioned))==nums,g['id'],f'Layout blanks differ: {positioned}')
                    if g['type'] in ('matching','multi'):check(bool(g.get('options')),g['id'],'Missing options')
                    for q in g['questions']:
                        accepted=key['answers'].get(str(q['number']),[])
                        check(bool(accepted),g['id'],'Missing key')
                        options=q.get('options',g.get('options',[]))
                        if options:check(all(v in {o['value'] for o in options} for v in accepted),g['id'],f'Key not in choices Q{q["number"]}')
                        if g['type']=='choice':check(len(options)==3,g['id'],'Choice must have A/B/C')
                check(pn==list(range(p['number']*10-9,p['number']*10+1)),where,'Part question sequence')
                numbers+=pn
            for url in refs(t,'url'):
                if url.startswith('/library-assets/'):check((LIB/'assets'/Path(url).name).exists(),ident,'Missing image '+url)
            check(numbers==list(range(1,41)),ident,'40 questions required')
            canonical={n:v[0] for n,v in key['answers'].items()}
            score=grade(t,key,canonical,numbers)['score'];check(score==40,ident,f'Canonical score {score}')
            for m in key.get('multi',[]):
                reverse=canonical.copy();reverse.update(zip(map(str,m['numbers']),reversed(m['answers'])))
                check(grade(t,key,reverse,numbers)['score']==40,ident,'Multi-order scoring')
            records.append({'id':ident,'questions':len(numbers),'parts':len(t['parts']),'canonicalScore':score})
    report={'tests':len(records),'parts':sum(r['parts'] for r in records),'questions':sum(r['questions'] for r in records),
            'uniqueAudioFiles':len(hashes),'groups':dict(kinds),'layouts':dict(layout_counts),'errors':issues,'records':records,
            'scope':'Structural, SHA-256, native controls, canonical answers, unordered multi choices; not a substitute for editorial PDF/audio review.'}
    (LIB/'preparation/listening/audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2))
    return report

if __name__=='__main__':sys.exit(bool(audit()['errors']))
