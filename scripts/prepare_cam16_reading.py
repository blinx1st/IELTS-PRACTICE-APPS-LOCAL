"""Private Cambridge 16 reading import and source verification helpers.

Source PDFs are read only. OCR caches and source proofs remain local.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import statistics

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'library'
PREP = LIB / 'preparation' / 'cam16'

def source():
    folder = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.endswith('Cambridge'))
    return next((folder / 'CAMBRIDGE-16' / 'BAN_GOC').glob('*.pdf'))

def extract_one(number):
    import pymupdf
    target = PREP / f'p{number:03}.json'
    if target.exists():
        return number, 'cached'
    with pymupdf.open(source()) as doc:
        page = doc[number - 1]
        tp = page.get_textpage_ocr(language='eng', dpi=220, full=True,
            tessdata='library/preparation/tessdata')
        data = {'book': 16, 'file': source().relative_to(ROOT).as_posix(),
            'page': number, 'method': 'tesseract-eng', 'dpi': 220,
            'width': page.rect.width, 'height': page.rect.height,
            'rotation': page.rotation,
            'text': page.get_text('text', textpage=tp),
            'words': [list(w[:5]) for w in page.get_text('words', textpage=tp)],
            'blocks': [{'box': list(b[:4]), 'text': b[4]}
                for b in page.get_text('blocks', textpage=tp) if b[6] == 0]}
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')
    return number, 'ocr'

def extract(first, last, workers):
    PREP.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        for n, status in pool.map(extract_one, range(first, last + 1)):
            print(n, status, flush=True)
    lines = []
    for p in sorted(PREP.glob('p*.json')):
        d = json.loads(p.read_text(encoding='utf8'))
        markers = re.findall(r'READING\s+PASSAGE\s+\d|Questions?\s+\d+(?:\s*[-–—]\s*\d+)?|WRITING\s+TASK', d['text'], re.I)
        lines.append(f"p{d['page']:03}: {' | '.join(markers)} :: {d['text'][:110].replace(chr(10),' ')}")
    (PREP / 'overview.txt').write_text('\n'.join(lines), encoding='utf8')

CONFIG = [
 [(['Why we need to protect polar bears'],[17,18],[(19,1,7,'tfng'),(20,8,13,'completion')]),
  (['The Step Pyramid of Djoser'],[22,23],[(21,14,20,'matching'),(24,21,24,'completion'),(24,25,26,'multi')]),
  (['The future of work'],[25,26],[(27,27,30,'choice'),(28,31,34,'matching'),(29,35,40,'matching')])],
 [(['The White Horse of Uffington'],[39,40],[(41,1,8,'tfng'),(42,9,13,'completion')]),
  (['I contain multitudes'],[43,44],[(45,14,16,'choice'),(46,17,20,'matching'),(47,21,26,'ynng')]),
  (['How to make wise decisions'],[48,49],[(50,27,30,'choice'),(51,31,35,'matching'),(52,36,40,'tfng')])],
 [(['Roman shipbuilding and navigation'],[62,63],[(64,1,5,'tfng'),(65,6,13,'completion')]),
  (['Climate change reveals ancient artefacts in Norway’s glaciers'],[66,67],[(68,14,19,'matching'),(68,20,22,'completion'),(69,23,24,'multi'),(69,25,26,'multi')]),
  (['Plant ‘thermometer’ triggers springtime growth by measuring night-time heat'],[70,71],[(72,27,32,'tfng'),(72,33,37,'matching'),(73,38,40,'completion')])],
 [(['Roman tunnels'],[83,84],[(85,1,6,'completion'),(86,7,10,'tfng'),(86,11,13,'short')]),
  (['Changes in reading habits'],[87,88],[(89,14,17,'choice'),(90,18,22,'matching'),(90,23,26,'ynng')]),
  (['Attitudes towards Artificial Intelligence'],[92,93],[(91,27,32,'matching'),(94,33,35,'choice'),(95,36,40,'ynng')])],
]
KEYS = [
 'FALSE|FALSE|NG|TRUE|TRUE|FALSE|TRUE|violent|tool|meat|photographer|game|frustration|iv|vii|ii|v|i|viii|vi|city|priests|trench|location|B|D|B|D|C|D|G|E|C|F|B|A|C|A|B|C',
 'TRUE|NG|TRUE|FALSE|FALSE|TRUE|TRUE|NG|Ridgeway|documents|soil|fertility|Rhiannon|D|C|A|G|B|H|E|YES|NO|NG|YES|NG|NO|B|C|B|D|D|A|C|F|G|FALSE|NG|NG|TRUE|TRUE',
 'FALSE|NG|FALSE|TRUE|TRUE|lightweight|bronze|levels|hull|triangular|music|grain|towboats|D|C|F|H|G|B|microorganisms~micro-organisms|reindeer|insects|B|C|A|C|NG|TRUE|TRUE|NG|FALSE|FALSE|H|D|G|C|A|warm~warm winter|summer|mustard plant~mustard plants~mustard',
 'posts|canal|ventilation|lid|weight|climbing|FALSE|NG|FALSE|TRUE|gold|architect~architect’s~architect\'s~architect name~architect’s name~architect\'s name~the architect~the architect’s~the architect\'s|harbour~harbor~the harbour~the harbor|A|B|D|B|D|H|F|B|C|YES|NO|NG|YES|iii|vi|ii|i|vii|v|C|B|A|NO|NG|YES|NO|YES',
]
MULTI = {1:[([25,26],['B','D'])],3:[([23,24],['B','C']),([25,26],['A','C'])]}

def load(number):
    return json.loads((PREP / f'p{number:03}.json').read_text(encoding='utf8'))

def repair(text):
    text = text.replace('IELTSXpress.com','')
    text = re.sub(r'Al(?=[’\'s\s,.?!:;—-]|$)', 'AI', text)
    text = text.replace('APOoB','APoB').replace('ganat','qanat').replace('numberofjobs','number of jobs')
    text = text.replace('Cevlik','Çevlik').replace('Pilo','Pilø').replace('Early lron','Early Iron')
    text = text.replace('to-be built','to be built').replace('Iron Age”','Iron Age*').replace('Bronze Age”','Bronze Age*')
    for a,b in {'ofclimate':'of climate','ofpolar':'of polar','oftheir':'of their','ofthe':'of the','ofthis':'of this',
        'ofheart':'of heart','ofbone':'of bone','ofa ':'of a ','ofmeat':'of meat','andjumping':'and jumping',
        'Ifclimate':'If climate','ofthem':'of them','ofhuman':'of human','ofmicrobes':'of microbes','ofYong':'of Yong',
        'playa ':'play a ','ofWaterloo':'of Waterloo','ona variety':'on a variety','ofwisdom':'of wisdom','adoptinga':'adopting a',
        'theirjob':'their job','ifyou':'if you','anda ':'and a ','ofNaples':'of Naples','ofyears':'of years','ofphytochromes':'of phytochromes',
        'secondjob':'second job','Ifa ':'If a ','stuffthey':'stuff they','oflow':'of low','offthe':'off the',
        'bya ':'by a ','asa ':'as a ','area fascinating':'are a fascinating','buildinga':'building a','offthem':'off them',
        'ofjobs':'of jobs','ofknowledge':'of knowledge','ofnew':'of new','causesof':'causes of','meana ':'mean a ',
        'ofunemployment':'of unemployment','ofAI':'of AI','ofa ':'of a ','ifnot':'if not','ofadvance':'of advance',
        'ofpatrons':'of patrons','skima ':'skim a ','AsUCLA':'As UCLA','halfofthe':'half of the','conducteda':'conducted a',
        'ofwhether':'of whether','ofWatson':'of Watson','ifWatson':'if Watson','ofresponsibility':'of responsibility',
        'informedby':'informed by','ina study':'in a study','Arecent':'A recent','Weshould':'We should',
        'areference':'a reference','adistance':'a distance','anemblem':'an emblem','arepresentation':'a representation',
        'Abasic':'A basic','Itcan':'It can','Itis':'It is','acontroversial':'a controversial','arecommended':'a recommended',
        'adifficulty':'a difficulty','numberof':'number of','ofpeople':'of people','itis':'it is',
        'Adifficult':'A difficult','Aking':'A king','Asingle':'A single','Apyramid':'A pyramid',
        'Ifthe':'If the','ofjob':'of job'}.items():
        text=re.sub(r'\b'+re.escape(a),lambda _:b,text)
    return text

def rows(number, top=40, bottom=655):
    d=load(number); result=[]
    for w in sorted((w for w in d['words'] if top <= w[1] < bottom),key=lambda w:(w[1],w[0])):
        if result and abs(w[1]-min(x[1] for x in result[-1])) < 3:result[-1].append(w)
        else:result.append([w])
    return [{'text':repair(' '.join(w[4] for w in sorted(r,key=lambda w:w[0]))),
        'top':min(w[1] for w in r),'bottom':max(w[3] for w in r)} for r in result]

def image(number, slug, top=0, bottom=None):
    import pymupdf
    from PIL import Image
    target=LIB/'assets'/f'cam16-r-{slug}.webp'
    if target.exists():return {'url':'/library-assets/'+target.name,'page':number}
    with pymupdf.open(source()) as doc:
        p=doc[number-1]
        pix=p.get_pixmap(dpi=155,clip=pymupdf.Rect(0,max(0,top),p.rect.width,min(bottom or p.rect.height,p.rect.height)),alpha=False)
        Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(target,'WEBP',quality=90)
    return {'url':'/library-assets/'+target.name,'page':number}

def passage_text(test, pn, pages, title):
    # Start/end coordinates are source-led: illustration, title, subtitle and
    # footnote lines are retained separately instead of entering the body.
    first_y={17:205,22:84,25:154,39:329,43:180,48:154,62:201,66:155,70:238,83:252,87:184,92:86}
    # Subtitles are part of the source and remain visible as introductory text.
    intro = {(2,2):'Wendy Moore reviews Ed Yong’s book about microbes',
        (3,3):'A photoreceptor molecule in plant cells has been found to have a second job as a thermometer after dark — allowing plants to read seasonal temperature changes. Scientists say the discovery could help breed crops that are more resilient to the temperatures expected to result from climate change',
        (4,1):'The Romans, who once controlled areas of Europe, North Africa and Asia Minor, adopted the construction techniques of other civilizations to build tunnels in their territories',
        (4,2):'What are the implications of the way we read today?'}
    pars=[]
    if (test,pn) in intro:pars.append({'text':intro[(test,pn)]})
    for ix,n in enumerate(pages):
        body=rows(n,first_y[n] if ix==0 else 45)
        previous=None; buf=[]; current_label=None
        def flush():
            nonlocal buf,current_label
            if buf:
                text=repair(' '.join(buf).strip())
                # A line-end hyphen joining a compound remains hyphenated.
                text=re.sub(r'([A-Za-z])-\s+([a-z])',r'\1-\2',text)
                p={'text':text}
                if current_label:p['label']=current_label
                if not current_label and pars and ix and not buf[0][0].isupper() and not pars[-1]['text'].endswith(('.', '?', '!', '.”','.’')):
                    pars[-1]['text']+=' '+p['text']
                else:pars.append(p)
            buf=[];current_label=None
        for row in body:
            line=row['text']
            if n==39 and row['top']>=640:continue
            if n==40 and row['top']>=600:continue
            if n==66 and row['top']>=620:continue
            match=re.match(r'^([A-H])(?:[_—]+|\s+)(.*)$',line)
            # Section letters are in the margin; ordinary sentence-initial
            # 'A' in unlabelled passages must never become a paragraph label.
            labelled=(test,pn) in [(1,2),(3,2),(3,3),(4,3)]
            label=match[1] if labelled and match else None
            if labelled and re.fullmatch('[A-H][_—]*',line):label=line[0];line=''
            elif label:line=match[2].lstrip('_— ')
            if label or (previous is not None and row['top']-previous['bottom']>4.8):flush()
            if label:current_label=label
            if line:buf.append(line)
            previous=row
        flush()
    # Paragraph boundaries hidden inside OCR text blocks are restored from the
    # reviewed printed page, especially where the scan's paragraph gap is small.
    if (test,pn)==(2,1):
        new=[]
        for p in pars:
            chunks=p['text'].split(' Nevertheless, the horse')
            new.append({**p,'text':chunks[0]})
            if len(chunks)>1:new.append({'text':'Nevertheless, the horse'+chunks[1]})
        pars=new
        pars.extend({'text':t} for t in [
            '*Iron Age: a period (in Britain 800 BCE – 43 CE) that is characterised by the use of iron tools',
            '*Bronze Age: a period (in Britain c. 2,500 BCE – 800 BCE) that is characterised by the development of bronze tools',
            '**Neolithic: a period (in Britain c. 4,000 BCE – c. 2,500 BCE) that is significant for the spread of agricultural practices, and the use of stone tools',
            '***Celtic: an ancient people who migrated from Europe to Britain before the Romans'])
    if (test,pn)==(3,2):pars.extend({'text':t} for t in [
        '*Viking Age: a period of European history from around 700 CE to around 1050 CE when Scandinavian Vikings migrated throughout Europe by means of trade and warfare',
        '**The Stone Age: a period in early history that began about 3.4 million years ago'])
    for i,p in enumerate(pars,1):p['id']=f'p{pn}-para{i}'
    return pars

def group_text(page,lo,hi):
    d=load(page)
    text=repair(d['text'])
    text=re.sub(r'(?m)^\s*(?:Test\s*\d|Reading|IELTSXpress\.com)\s*$','',text)
    pattern=re.compile(r'(?m)^Questions?\s+(\d+)(?:\s*(?:[-–—]|and)\s*(\d+))?[^\n]*')
    matches=list(pattern.finditer(text))
    m=next(m for m in matches if int(m[1])==lo)
    end=next((x.start() for x in matches if x.start()>m.start()),len(text))
    body=text[m.end():end].strip()
    # Printed key-page links and publisher footers are not question content.
    body=re.split(r'\n(?:[<>»=—-]*\s*[|/@Q©]|IELTSXpress|Tham gia)',body)[0]
    body=re.sub(r'\n\s*\d{1,3}\s*$','',body).strip()
    body=re.sub(r'NOT GIVEN[_]+','NOT GIVEN',body)
    return body

def options(text,letters):
    # Standalone option letters can have scanner underscores/dots attached.
    pat=re.compile(r'(?m)^\s*('+ '|'.join(sorted(letters,key=len,reverse=True)) +r')[_.-]*(?:\s+|(?=[A-Z][a-z]))')
    matches=list(pat.finditer(text)); out=[]
    for i,m in enumerate(matches):
        label=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        label=re.sub(r'\s+',' ',label).strip(' _')
        out.append({'value':m[1],'label':label})
    return out

def group(test,pn,gi,page,lo,hi,kind):
    sys.path.insert(0,str(ROOT/'scripts'))
    import prepare_library as common
    text=group_text(page,lo,hi)
    ins,body=common.split_directions(text)
    # split_directions expects a header but accepts a header-free body too.
    number_pat=re.compile(r'(?m)^\s*(\d{1,2})[._]*\s+')
    matches=[m for m in number_pat.finditer(body) if lo<=int(m[1])<=hi]
    qs=[]
    for n in range(lo,hi+1):
        m=next((m for m in matches if int(m[1])==n),None)
        tail=body[m.end():next((x.start() for x in matches if x.start()>m.start()),len(body))] if m else ''
        if kind=='choice':
            opts=options(tail,list('ABCD'))
            prompt=re.split(r'(?m)^\s*A[_.-]*\s+',tail)[0]
            qs.append({'number':n,'text':re.sub(r'\s+',' ',prompt).strip(' _‘'),'options':opts})
        else:qs.append({'number':n,'text':repair(re.sub(r'\s+',' ',tail).strip(' _')) if kind in ['tfng','ynng','short','matching'] else ''})
    g={'id':f'cam16-t{test}-p{pn}-g{gi}','type':kind,'heading':f'Questions {lo}–{hi}',
       'instructions':ins,'body':body,'questions':qs,'sourceImages':[]}
    if kind in ['tfng','ynng','choice','short']:g['body']=''
    if kind in ['completion','short']:
        g['wordLimit']=2 if 'TWO WORDS' in ins else 1
        g['allowNumber']=False
    if kind=='matching':
        if 'heading' in ins.lower():
            g['options']=options(body.split('List of Headings',1)[-1].split(str(lo)+'\n')[0],['i','ii','iii','iv','v','vi','vii','viii','ix'])
            g['layout']={'kind':'matrix','matchingKind':'headings','rows':[{'number':n,'text':('Paragraph ' if test==1 else 'Section ')+chr(65+n-lo)} for n in range(lo,hi+1)]}
            g['body']=''
        elif 'Which section' in ins:
            g['options']=[{'value':c,'label':c} for c in 'ABCDEFGH']
            g['layout']={'kind':'matrix','matchingKind':'paragraphs','rows':[]}
            for n in range(lo,hi+1):
                m=next(m for m in matches if int(m[1])==n)
                t=body[m.end():next((x.start() for x in matches if x.start()>m.start()),len(body))]
                g['layout']['rows'].append({'number':n,'text':re.sub(r'\s+',' ',t).strip()})
            g['body']=''
        else:
            opttext=body.split('List of people')[-1] if 'List of people' in body else body
            g['options']=options(opttext,list('ABCDEFGHIJ'))
    if kind=='multi':
        g['choose']=hi-lo+1
        g['options']=options(body,list('ABCDE'))
        g['body']=re.split(r'(?m)^\s*A[_-]*\s+',body)[0].strip()
    coords=rows(page,0,655)
    start=next(r['top'] for r in coords if re.match(rf'Questions?\s+{lo}\b',r['text']))
    next_top=next((r['top'] for r in coords if r['top']>start+2 and re.match(r'Questions?\s+\d',r['text'])),655)
    g['sourceImages']=[image(page,f't{test}-p{pn}-g{gi}-source',max(0,start-5),next_top-3)]
    return g

COMPLETIONS = {
 (1,8):'''Reasons why polar bears should be protected
People think of bears as unintelligent and 8 ..........
However, this may not be correct. For example:
• In Tennoji Zoo, a bear has been seen using a branch as a 9 .......... . This allowed him to knock down some 10 ..........
• A wild polar bear worked out a method of reaching a platform where a 11 .......... was located.
• Polar bears have displayed behaviour such as conscious manipulation of objects and activity similar to a 12 ..........
Bears may also display emotions. For example:
• They may make movements suggesting 13 .......... if disappointed when hunting.
• They may form relationships with other species.''',
 (1,21):'''The Step Pyramid of Djoser
The complex that includes the Step Pyramid and its surroundings is considered to be as big as an Egyptian 21 .......... of the past. The area outside the pyramid included accommodation that was occupied by 22 .......... , along with many other buildings and features.
A wall ran around the outside of the complex and a number of false entrances were built into this. In addition, a long 23 .......... encircled the wall. As a result, any visitors who had not been invited were cleverly prevented from entering the pyramid grounds unless they knew the 24 .......... of the real entrance.''',
 (1,31):'''The ‘algorithmication’ of jobs
Stella Pachidi of Cambridge Judge Business School has been focusing on the ‘algorithmication’ of jobs which rely not on production but on 31 .......... .
While monitoring a telecommunications company, Pachidi observed a growing 32 .......... on the recommendations made by AI, as workers begin to learn through the ‘algorithm’s eyes’. Meanwhile, staff are deterred from experimenting and using their own 33 .......... , and are therefore prevented from achieving innovation.
To avoid the kind of situations which Pachidi observed, researchers are trying to make AI’s decision-making process easier to comprehend, and to increase users’ 34 .......... with regard to the technology.''',
 (2,9):'''The Uffington White Horse
The location of the Uffington White Horse:
• a distance of 2.5 km from Uffington village
• near an ancient road known as the 9 ..........
• close to an ancient cemetery that has a number of burial mounds
Dating the Uffington White Horse:
• first reference to White Horse Hill appears in 10 .......... from the 1070s
• horses shown on coins from the period 100 BCE – 1 BCE are similar in appearance
• according to analysis of the surrounding 11 .......... , the Horse is Late Bronze Age / Early Iron Age
Possible reasons for creation of the Uffington White Horse:
• an emblem to indicate land ownership
• formed part of an ancient ritual
• was a representation of goddess Epona – associated with protection of horses and 12 ..........
• was a representation of a Welsh goddess called 13 ..........''',
 (2,17):'''We should be more tolerant of microbes
Yong’s book argues that we should be more tolerant of microbes. Many have a beneficial effect, and only a relatively small number lead to 17 .......... . And although it is misleading to think of microbes as ‘friendly’, we should also stop thinking of them as the enemy. In fact, we should accept that our relationship with microbes is one based on 18 .......... .
New research shows that microbes have numerous benefits for humans. Amongst other things, they aid digestion, remove poisons, produce vitamins and may even help reduce obesity. However, there is a growing problem. Our poor 19 .......... , our overuse of antibiotics, and our excessive focus on 20 .......... are upsetting the bacterial balance and may be contributing to the huge increase in allergies and immune system problems.''',
 (2,31):'''The characteristics of wise reasoning
Igor Grossmann and colleagues have established four characteristics which enable us to make wise decisions. It is important to have a certain degree of 31 .......... regarding the extent of our knowledge, and to take into account 32 .......... which may not be the same as our own. We should also be able to take a broad 33 .......... of any situation. Another key characteristic is being aware of the likelihood of alterations in the way that people relate to each other.
Grossmann also believes that it is better to regard scenarios with 34 .......... . By avoiding the first-person perspective, we focus more on 35 .......... and on other moral ideals, which in turn leads to wiser decision-making.''',
 (3,6):'''Warships and merchant ships
Warships were designed so that they were 6 .......... and moved quickly. They often remained afloat after battles and were able to sail close to land as they lacked any additional weight. A battering ram made of 7 .......... was included in the design for attacking and damaging the timber and oars of enemy ships. Warships, such as the ‘trireme’, had rowers on three different 8 .......... .
Unlike warships, merchant ships had a broad 9 .......... that lay far below the surface of the sea. Merchant ships were steered through the water with the help of large rudders and a tiller bar. They had both square and 10 .......... sails. On merchant ships and warships, 11 .......... was used to ensure rowers moved their oars in and out of the water at the same time.
Quantities of agricultural goods such as 12 .......... were transported by merchant ships to two main ports in Italy. The ships were pulled to the shore by 13 .......... . When the weather was clear and they could see islands or land, sailors used landmarks that they knew to help them navigate their route.''',
 (3,20):'''Interesting finds at an archaeological site
Organic materials such as animal skins and textiles are not discovered very often at archaeological sites. They have little protection against 20 .......... , which means that they decay relatively quickly. But this is not always the case. If temperatures are low enough, fragile artefacts can be preserved for thousands of years.
A team of archaeologists have been working in the mountains in Oppland in Norway to recover artefacts revealed by shrinking ice cover. In the past, there were trade routes through these mountains and 21 .......... gathered there in the summer months to avoid being attacked by 22 .......... on lower ground. The people who used these mountains left things behind and it is those objects that are of interest to archaeologists.''',
 (3,38):'''38 Daffodils are likely to flower early in response to .......... weather.
39 If ash trees come into leaf before oak trees, the weather in .......... will probably be wet.
40 The research was carried out using a particular species of .......... .''',
 (4,18):'''Studies on digital screen use
There have been many studies on digital screen use, showing some 18 .......... trends. Psychologist Anne Mangen gave high-school students a short story to read, half using digital and half using print mediums. Her team then used a question-and-answer technique to find out how 19 .......... each group’s understanding of the plot was. The findings showed a clear pattern in the responses, with those who read screens finding the order of information 20 .......... to recall.
Studies by Ziming Liu show that students are tending to read 21 .......... words and phrases in a text to save time. This approach, she says, gives the reader a superficial understanding of the 22 .......... content of material, leaving no time for thought.''',
}

def reviewed_group(g,test,lo):
    if (test,lo) in COMPLETIONS:
        g['body']=COMPLETIONS[(test,lo)]
        for q in g['questions']:q['text']=''
    if (test,lo)==(3,38):
        g['body']=''
        for q,t in zip(g['questions'],['Daffodils are likely to flower early in response to .......... weather.',
            'If ash trees come into leaf before oak trees, the weather in .......... will probably be wet.',
            'The research was carried out using a particular species of .......... .']):q['text']=t
    if (test,lo)==(1,8):
        parts=['People think of bears as unintelligent and ',{'number':8},'\n\nHowever, this may not be correct. For example:\n\n• In Tennoji Zoo, a bear has been seen using a branch as a ',{'number':9},'. This allowed him to knock down some ',{'number':10},'\n\n• A wild polar bear worked out a method of reaching a platform where a ',{'number':11},' was located.\n\n• Polar bears have displayed behaviour such as conscious manipulation of objects and activity similar to a ',{'number':12},'\n\nBears may also display emotions. For example:\n\n• They may make movements suggesting ',{'number':13},' if disappointed when hunting.\n\n• They may form relationships with other species.']
        g['layout']={'kind':'table','rows':[{'cells':[{'header':True,'content':['Reasons why polar bears should be protected']}]},{'cells':[{'content':parts}]}]}
    if (test,lo)==(1,25):g['options']=[{'value':v,'label':t} for v,t in zip('ABCDE',[
        'Initially he had to be persuaded to build in stone rather than clay.',
        'There is disagreement concerning the length of his reign.',
        'He failed to appreciate Imhotep’s part in the design of the Step Pyramid.',
        'A few of his possessions were still in his tomb when archaeologists found it.',
        'He criticised the design and construction of other pyramids in Egypt.'])]
    if (test,lo)==(1,35):
        g['options']=[{'value':v,'label':t} for v,t in zip('ABC',['Stella Pachidi','Hamish Low','Ewan McGaughey'])]
        g['body']=''
        g['questions'][-1]['text']='Authorities should take measures to ensure that there will be adequately paid work for everyone.'
    if (test,lo)==(2,27):
        g['questions'][0]['options']=[{'value':v,'label':t} for v,t in zip('ABCD',[
            'Wisdom appears to be unique to the human race.','A basic assumption about wisdom may be wrong.',
            'Concepts of wisdom may depend on the society we belong to.','There is still much to be discovered about the nature of wisdom.'])]
        g['questions'][-1]['options']=[{'value':v,'label':t} for v,t in zip('ABCD',[
            'a difficulty encountered when attempting to reason wisely','an example of the type of person who is likely to reason wisely',
            'a controversial view about the benefits of reasoning wisely','a recommended strategy that can help people to reason wisely'])]
    if (test,lo)==(2,31):g['options']=[{'value':v,'label':t} for v,t in zip('ABCDEFGHIJ',[
        'opinions','confidence','view','modesty','problems','objectivity','fairness','experiences','range','reasons'])]
    if (test,lo)==(4,18):g['options']=[{'value':v,'label':t} for v,t in zip('ABCDEFGH',['fast','isolated','emotional','worrying','many','hard','combined','thorough'])]
    if (test,lo)==(4,1):
        g['instructions']='Label the diagrams below.\nChoose ONE WORD ONLY from the passage for each answer.\nWrite your answers in boxes 1–6 on your answer sheet.'
        g['body']=''
        g['renderMode']='source'
    for q in g['questions']:
        q['text']=re.sub(r'([A-Za-z])-\s+([a-z])',r'\1-\2',q['text'])
    return g

def assemble():
    source_hash=hashlib.sha256(source().read_bytes()).hexdigest(); report=[]
    for t,conf in enumerate(CONFIG,1):
        test={'id':f'cam16-test{t}','skill':'reading','book':16,'test':t,'title':f'Cambridge 16 · Test {t}',
              'version':'2026-10-21.1','verification':{'status':'verified',
                'note':'All 3 passages and 40 questions, options, instructions and word limits compared with rendered supplied PDF pages. OCR word joins, paragraph boundaries, source accents and unreadable completion blanks corrected. Private key separately read against printed source key.',
                'reviewReport':'library/preparation/cam16/reading-review.json'},'passages':[]}
        for pn,(title,pages,specs) in enumerate(conf,1):
            p={'id':f'cam16-test{t}-p{pn}','number':pn,'title':title[0],
               'paragraphs':passage_text(t,pn,pages,title[0]),'groups':[],
               'sourceImages':[image(n,f't{t}-p{pn}-reading-{n:03}') for n in pages],
               'sourcePages':[{'file':source().relative_to(ROOT).as_posix(),'page':n} for n in sorted(set(pages+[x[0] for x in specs]))]}
            for gi,spec in enumerate(specs,1):p['groups'].append(reviewed_group(group(t,pn,gi,*spec),t,spec[1]))
            test['passages'].append(p)
        raw=json.dumps(test,ensure_ascii=False,indent=2)+'\n'
        (LIB/'tests'/f"{test['id']}.json").write_text(raw,encoding='utf8')
        override=LIB/'preparation'/'overrides'/f"{test['id']}.json"
        override.parent.mkdir(parents=True,exist_ok=True)
        override.write_text(raw,encoding='utf8')
        answers={str(n):['NOT GIVEN' if a=='NG' else a for a in v.split('~')] for n,v in enumerate(KEYS[t-1].split('|'),1)}
        assert len(answers)==40
        key={'id':test['id'],'version':'1','answers':answers,'multi':[{'numbers':n,'answers':a} for n,a in MULTI.get(t,[])],
             'provenance':{'source':source().relative_to(ROOT).as_posix(),'sha256':source_hash,'pdfPage':121+2*t,
                'verification':'visual-source-key-review','scope':'answer-key-only','questionContentVerified':True}}
        (LIB/'keys'/f"{test['id']}.json").write_text(json.dumps(key,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        report.append({'id':test['id'],'passages':3,'questions':sum(len(g['questions']) for p in test['passages'] for g in p['groups'])})
        print(test['id'],report[-1],flush=True)
    (PREP/'reading-report.json').write_text(json.dumps({'tests':report,'sourceSha256':source_hash},indent=2)+'\n',encoding='utf8')

def audit():
    sys.path.insert(0,str(ROOT))
    from backend.scoring import grade, within_limit
    errors=[];tests=[]
    for t in range(1,5):
        item=json.loads((LIB/'tests'/f'cam16-test{t}.json').read_text(encoding='utf8'))
        key=json.loads((LIB/'keys'/f'cam16-test{t}.json').read_text(encoding='utf8'))
        numbers=[q['number'] for p in item['passages'] for g in p['groups'] for q in g['questions']]
        if sorted(numbers)!=list(range(1,41)):errors.append(f'Test {t} numbering')
        for p in item['passages']:
            for ent in [p]+p['groups']:
                for ref in ent['sourceImages']:
                    if not (LIB/'assets'/ref['url'].split('/')[-1]).exists():errors.append(f'Missing {ref}')
            for g in p['groups']:
                for q in g['questions']:
                    if g['type']=='choice' and [o['value'] for o in q['options']]!=list('ABCD'):errors.append(f'Bad options {t}/{q["number"]}')
                    if g['type'] in ['choice','tfng','ynng','short'] and not q['text']:errors.append(f'Empty prompt {t}/{q["number"]}')
                    for a in key['answers'][str(q['number'])]:
                        if not within_limit(a,g):errors.append(f'Key word limit {t}/{q["number"]}: {a}')
                if g['type']=='matching':
                    allowed={o['value'] for o in g['options']}
                    for q in g['questions']:
                        if key['answers'][str(q['number'])][0] not in allowed:errors.append(f'Matching option {t}/{q["number"]}')
        mark=grade(item,key,{n:a[0] for n,a in key['answers'].items()},numbers)
        if mark['score']!=40:errors.append(f'Perfect key score {t}: {mark["score"]}')
        if (LIB/'preparation'/'overrides'/f'cam16-test{t}.json').read_bytes()!=(LIB/'tests'/f'cam16-test{t}.json').read_bytes():errors.append(f'Override mismatch {t}')
        tests.append({'id':item['id'],'passages':3,'questions':40,'perfectKeyScore':mark['score'],
                      'contentSha256':hashlib.sha256((LIB/'tests'/f'cam16-test{t}.json').read_bytes()).hexdigest(),
                      'keySha256':hashlib.sha256((LIB/'keys'/f'cam16-test{t}.json').read_bytes()).hexdigest()})
    result={'book':16,'skill':'reading','tests':tests,'passages':12,'questions':160,
            'status':'verified' if not errors else 'failed','errors':errors,
            'source':source().relative_to(ROOT).as_posix(),'sourceSha256':hashlib.sha256(source().read_bytes()).hexdigest(),
            'readingPdfPages':sorted({n for conf in CONFIG for _,pages,spec in conf for n in pages+[s[0] for s in spec]}),
            'keyPdfPages':[123,125,127,129],
            'visualEvidence':[f'library/preparation/cam16/proof-pair-{n:02}.jpg' for n in range(26)],
            'review':{'passages':'24 passage PDF pages compared against OCR/reconstructed paragraphs. All first and last lines, section A–H labels, paragraph gaps and source footnotes retained.',
                      'questions':'All 160 questions, 34 groups, option sets, numbering and printed word limits compared with the 28 rendered question PDF pages.',
                      'keys':'All 160 answers visually read from the 4 printed key pages; optional words/variants expanded and all multi answer groups recorded.',
                      'layouts':'Native single-column table T1 Q8–13; 2 heading matrices and 2 paragraph matrices. T4 Q1–6 retains original two source diagrams with separate Reading inputs.',
                      'limitations':'Source is a user supplied scan. Publisher resources online were not required. No study database or pre-existing attempt snapshots modified.'}}
    (PREP/'reading-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'tests':4,'passages':12,'questions':160,'errors':errors},ensure_ascii=False))
    if errors:raise SystemExit(1)

def main():
    os.chdir(ROOT)
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['extract','assemble','audit'])
    parser.add_argument('--first', type=int, default=1)
    parser.add_argument('--last', type=int, default=135)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    if args.command=='extract':extract(args.first, args.last, args.workers)
    elif args.command=='assemble':assemble()
    else:audit()

if __name__ == '__main__':
    main()
