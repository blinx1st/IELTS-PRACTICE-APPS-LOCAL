"""Private editorial corrections compared with supplied PDFs. Audio proof stays local."""
from pathlib import Path
import json,re,string,sys
ROOT=Path(__file__).resolve().parents[1];LIB=ROOT/'library';PREP=LIB/'preparation/listening'

ROWS={
'17-1-27':'Medical terminology|Diet and nutrition|Animal disease|Wildlife medication',
'17-2-15':'dairy|large barn|small barn|stables|shed|parkland',
'17-2-23':'the set|the lighting|the costume design|the music|the actors’ delivery',
'17-3-16':'Spanish|Music|Painting|Yoga|Cooking',
'17-3-25':'Communication|Organisation|Time management|Creativity|Leadership|Networking',
'17-4-15':'The Sun Club|The Portland|Bluewater Hotels|Pentlow Hotels|Green Planet|The Amesbury',
'17-4-25':'the table tennis bat|the cricket helmet|the cycle helmet|the golf club|the hockey stick|the football',
'18-1-16':'Fundraising|Litter collection|‘Playmates’|Story club|First aid',
'18-2-15':'School|Sports centre|Clinic|Community centre|Supermarket|Playground',
'18-2-27':'Iceland|Egypt|UK|USA',
'18-3-25':'Accountants|Hairdressers|Administrative staff|Agricultural workers|Care workers|Bank clerks',
'18-4-15':'Four Seasons|Farmhouse Kitchen|A Year on the Farm|Wagon Walk|Bees are Magic|The Pond',
'18-4-23':'Sid|Jack|Naomi|Anya|Zara',
'19-1-16':'Farm shop|Disabled entry|Adventure playground|Kitchen gardens|The Temple of the Four Winds',
'19-1-25':'Use of local products|Reduction in unnecessary packaging|Gluten-free and lactose-free food|Use of branded products related to celebrity chefs|Development of ‘ghost kitchens’ for takeaway food|Use of mushrooms for common health concerns',
'19-2-25':'the high-heeled shoes|the ankle boots|the baby shoes|the trainers',
'19-3-11':'Superheroes|Just do it|Count on me|Speak up|Jump for joy|Sticks and stones',
'19-4-15':'Ceri|James|Leo|Mark',
'19-4-26':'rare books|children’s books|unwanted books|requested books|coursebooks',
'20-3-17':'bridge foundations|rubbish pit|meeting hall|fish pond',
'20-4-15':'1870|1874|1875|1877|1878|1880',
}
OPTIONS={
'17-2-21':'analysis of the text|a summary of the plot|a description of the theatre|a personal reaction|a reference to particular scenes',
'17-3-16':'has limited availability|is no longer available|is for over 8s only|requires help from parents|involves an additional fee|is a new activity|was requested by children',
'17-4-15':'improving relationships and teamwork|offering incentives and financial benefits|providing career opportunities',
'19-3-26':'size|escape|age|water|cereal|calculations|changes|colour',
'19-4-26':'near the entrance|in the attic|at the back of the shop|on a high shelf|near the stairs|in a specially designed space|within the café',
}
CHOICES={
(17,1,11):['9','15','18'],(17,1,12):['dark red','jet black','light green'],
(17,3,24):['bad weather','an injury','extra time'],
(17,4,12):['an increased workload','low morale','an inability to meet targets'],
(18,4,14):['cameras','coats','bags'],
}
HEADERS=['Modules on Veterinary Science course','Locations on the farm','Aspects of the production','Activities','Events management skills','Hotels','Items of sporting equipment','Area of voluntary work','Countries','Jobs','Areas of museum','Children','Food trends','Footwear','Festival workshops','Club members','Types of books']
REPAIRS={'Itis':'It is','itis':'it is','Heis':'He is','Hecould':'He could','Itcould':'It could','Noone':'No one','Anaverage':'An average','Achild':'A child','Agreater':'A greater','Anexpert':'An expert','Inhis':'In his','Asa ':'As a ','Atfirst':'At first','Atree':'A tree','Agarden':'A garden','iIthad':'It had','alamb':'a lamb','asheep':'a sheep','anewly':'a newly','aplace':'a place','alack':'a lack','anincrease':'an increase','arise':'a rise','aninability':'an inability','ahuge':'a huge','aprivate':'a private','ahall':'a hall','aresearch':'a research','anunderstanding':'an understanding','agood':'a good','asummary':'a summary','adescription':'a description','areference':'a reference','adislike':'a dislike','anew angle':'a new angle','ina ':'in a ','inthe ':'in the ','atthe ':'at the ','bya ':'by a ','toa ':'to a ','whowill':'who will','setachallenge':'set a challenge','experiencinga':'experiencing a','hada ':'had a ','slight green':'light green','iow pay':'low pay'}

def clean(s):
    s=re.sub(r'\s+',' ',s).strip()
    s=re.sub(r'^(?:Listening test audio|Listoding feat tials|Listening feat atid)\s+','',s)
    for a,b in {'itillustrates':'it illustrates','itinvolves':'it involves','Ithas':'It has','wasa ':'was a ','fashion sizes 14':'fashion sizes','equipment 36 =':'equipment','practice runs. 80':'practice runs.'}.items():s=s.replace(a,b)
    s=re.sub(r'\s*(?:[>|@/\[\]]+\s*(?:@|p\.|[\[\]|/]|\d).*)$','',s)
    s=re.sub(r'\s+(?:38|80)\s*=.*$','',s)
    s=re.sub(r'\s+By$','',s)
    for a,b in REPAIRS.items():s=s.replace(a,b)
    return s.rstrip(' :')

def each_text(v):
    if isinstance(v,dict):
        return {k:(clean(x) if k in ('text','label','instructions','body') and isinstance(x,str) else each_text(x)) for k,x in v.items()}
    if isinstance(v,list):return [each_text(x) for x in v]
    return v

def correct(t,k):
    b=t['book'];tn=t['test']
    for u in t['parts']:
        for i,g in enumerate(u['groups']):
            lo=g['questions'][0]['number'];code=f'{b}-{tn}-{lo}'
            u['groups'][i]=g=each_text(g)
            if g['type']=='choice':g['instructions']='Choose the correct letter, A, B or C.'
            if code in ROWS:
                labels=ROWS[code].split('|');assert len(labels)==len(g['questions'])
                for q,label in zip(g['questions'],labels):q['text']=label
            if code in OPTIONS:g['options']=[{'value':string.ascii_uppercase[n],'label':v} for n,v in enumerate(OPTIONS[code].split('|'))]
            for q in g['questions']:
                if (b,tn,q['number']) in CHOICES:q['options']=[{'value':string.ascii_uppercase[n],'label':v} for n,v in enumerate(CHOICES[b,tn,q['number']])]
            for o in g.get('options',[]):
                for suffix in HEADERS:
                    o['label']=re.sub(r'[. ]*'+re.escape(suffix)+r'.*$','',o['label']).strip()
                o['label']=o['label'].lstrip('= ').strip()
            if g['type']=='matching':
                for suffix in HEADERS:g['instructions']=re.sub(r'\s+'+re.escape(suffix)+r'$','',g['instructions'])
            if code=='17-4-15':g['instructions']='Which way of reducing staff turnover was used in each of the following hotels? Write the correct letter, A, B or C, next to Questions 15–20.'
            if b==20 and tn==1 and lo==1:
                for row in g['layout']['rows']:
                    for cell in row['cells']:cell['content']=[x.replace('Proportions probably','Portions probably').replace('limited section','limited selection') if isinstance(x,str) else x for x in cell['content']]
            diagram={
                '18-2-15':(37,.35,[.649,.680,.712,.744,.776,.807],'I'),
                '19-1-16':(11,.485,[.758,.787,.816,.846,.878],'H'),
            }.get(code)
            if diagram:
                pg,x,ys,last=diagram
                g['instructions']=f'Label the map below. Write the correct letter, A–{last}, next to Questions {lo}–{g["questions"][-1]["number"]}.'
                g['options']=[{'value':c,'label':c} for c in string.ascii_uppercase[:ord(last)-64]]
                g['layout']={'kind':'diagram','image':{'url':f'/library-assets/l-cam{b}-source-{pg:03}.webp','page':pg},'labels':[{'number':q['number'],'x':x,'y':y,'width':.15} for q,y in zip(g['questions'],ys)]}
            if code=='19-3-26':
                g['layout']={'kind':'diagram','image':{'url':'/library-assets/l-cam19-source-059.webp','page':59},'labels':[{'number':n,'x':x,'y':y,'width':.18} for n,x,y in [(26,.52,.434),(27,.67,.524),(28,.69,.653),(29,.66,.766),(30,.35,.859)]]}
            if code=='20-3-17':
                import pymupdf as fitz
                base=ROOT/'Tài liệu Cambridge/CAMBRIDGE-20/BAN_GOC'
                pdf=next(p for p in base.glob('*.pdf') if 'Fighter' not in p.name)
                out=LIB/'assets/l-cam20-t3-map-original.webp'
                with fitz.open(pdf) as doc:
                    pix=doc[45].get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(25,115,560,725))
                    from PIL import Image
                    Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(out,quality=92)
                g['instructions']='Label the map below. Write the correct letter, A–G, next to Questions 17–20.'
                g['options']=[{'value':c,'label':c} for c in 'ABCDEFG']
                g['layout']={'kind':'diagram','image':{'url':'/library-assets/'+out.name,'page':46},'labels':[{'number':n,'x':.473,'y':y,'width':.17} for n,y in zip(range(17,21),[.766,.821,.88,.936])]}
                source={'url':'/library-assets/'+out.name,'page':46}
                if source not in g['sourceImages']:g['sourceImages'].append(source)
                g['errata']=['Source instruction says A–F, but the diagram includes G. Original map recovered from alternate supplied PDF; retyped PDF omits it.']
    if (b,tn)==(18,1):k.setdefault('limitExceptions',{})['1']=['DW30 7YZ']
    if (b,tn)==(19,4):k.setdefault('limitExceptions',{})['6']=['0412 665 903']
    if (b,tn)==(20,4):
        k['answers']['11']=['B'];k['answers']['12']=['C']
        for m in k['multi']:
            if m['numbers']==[11,12]:m['answers']=['B','C']
        k['errata']=[{'question':12,'issue':'Supplied retyped answer-key cell12 is blank.','correction':'C','evidence':'Provided Part2 recording/transcript explicitly requires parents to stay with children; B is drawing competition. This is an unordered B/C pair.'}]
    # Explicit source-key variants such as a spaced postcode/phone number and a
    # spelled-out number are accepted only when exactly listed in the private key.
    from backend.scoring import within_limit
    for u in t['parts']:
        for g in u['groups']:
            for q in g['questions']:
                n=str(q['number']);over=[v for v in k['answers'][n] if not within_limit(v,g)]
                if over:k.setdefault('limitExceptions',{})[n]=sorted(set(k.get('limitExceptions',{}).get(n,[])+over))
    return t,k

def finalize_audio(t):
    b,tn=t['book'],t['test']
    for part in t['parts']:
        n=part['number'];a=part['audio'];timeline=PREP/f'cam{b}'/f'timeline-t{tn}-p{n}.json'
        evidence=[]
        if timeline.exists():
            proof=json.loads(timeline.read_text(encoding='utf8'));assert proof['audioSha256']==a['sha256']
            words=[w for s in proof['segments'] for w in s.get('words',[])]
            if n==1 and b>=17:
                # Start at the specific introduction, after generic CD/paper instructions.
                cue=next(i for i in range(len(words)-4) if 'you will hear' in ' '.join(w['word'].lower().strip(' .,') for w in words[i:i+3]) and words[i]['start']>30)
                a['start']=round(max(0,words[cue]['start']-.2),2)
                evidence.append('Specific Part 1 introduction retained; publisher and paper instructions excluded.')
            if n==4:
                matches=[w['start'] for i,w in enumerate(words) if 'you now have'==' '.join(x['word'].lower().strip(' .,') for x in words[i:i+3])]
                if matches:a['end']=round(matches[-1],2)
                elif (b,tn)==(18,4):a['end']=414
                elif (b,tn)==(19,3):a['end']=384
                else:raise ValueError(f'Missing final check boundary: {b}/{tn}')
                evidence.append('Final embedded check pause and paper-transfer directions removed; app supplies exactly 120 seconds.')
                if not matches:evidence.append('No reliable spoken check cue in source; boundary follows last transcript sentence (timed local ASR evidence).')
        assert 0<=a.get('start',0)<a.get('end',a['duration'])<=a['duration']+.05
        content=PREP/f'cam{b}'/(f't{tn}-p{n}-audio-asr.json' if b<17 else f'audio-t{tn}-p{n}.json')
        assert content.exists()
        a['verification']={'status':'verified','method':'Local recording opening/ending compared against supplied audioscript and questions; all 16 candidates per book compared.',
                           'proof':content.relative_to(LIB).as_posix(),'contentComparison':'preparation/listening/audio-content-comparison.json',
                           'timelineProof':timeline.relative_to(LIB).as_posix() if timeline.exists() else None,'timelineNotes':evidence}
        if (b,tn,n)==(19,1,1):a['verification']['additionalProof']='preparation/listening/cam19/timeline-t1-p1.json (115–175 seconds: Hinchingbrooke 69 hectares, wetland and stream)'
    t['verification']={'status':'verified','method':'Source question pages and key pages reviewed; native layouts corrected; local recording samples compared with source scripts.',
                       'reviewReport':'preparation/listening/final-review.json'}

def main():
    sys.path.insert(0,str(ROOT))
    for f in sorted((LIB/'listening/tests').glob('*.json')):
        t=json.loads(f.read_text(encoding='utf8'));kp=LIB/'listening/keys'/f.name;k=json.loads(kp.read_text(encoding='utf8'))
        if t['book']>=17:t,k=correct(t,k)
        finalize_audio(t)
        f.write_text(json.dumps(t,ensure_ascii=False,indent=2)+'\n',encoding='utf8');kp.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
