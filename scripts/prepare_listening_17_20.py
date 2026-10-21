"""Local Cambridge Listening source extraction and reproducible preparation (17–20)."""
from __future__ import annotations
import concurrent.futures, hashlib, json, re, shutil, sys, urllib.request
from pathlib import Path
import pymupdf
from mutagen import File as AudioFile

ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT/'library'
PREP=LIB/'preparation'/'listening'
TESS=LIB/'preparation'/'tessdata'

def source(book):
    files=list((ROOT/'Tài liệu Cambridge'/f'CAMBRIDGE-{book}'/'BAN_GOC').glob('*.pdf'))
    if book==20:return next(p for p in files if 'IELTS Fighter' in p.name)
    return files[0]

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')

def cache_page(job):
    book,n=job
    dest=PREP/f'cam{book}'/f'p{n:03}.json'
    if dest.exists():return
    dest.parent.mkdir(parents=True,exist_ok=True)
    old=LIB/'preparation'/f'cam{book}'/f'p{n:03}.json'
    if book!=20 and old.exists():
        shutil.copyfile(old,dest);return
    src=source(book)
    with pymupdf.open(src) as doc:
        p=doc[n-1];raw=p.get_text()
        stripped=re.sub(r'(?m)^.*(?:ielts-fighter|Làm đề|Website tự|Tham gia group|facebook\.com).*$', '',raw)
        ocr=len(re.sub(r'\s','',stripped))<100
        tp=p.get_textpage_ocr(language='eng',dpi=220,full=True,tessdata=str(TESS.relative_to(ROOT))) if ocr else p.get_textpage()
        d={'book':book,'file':str(src.relative_to(ROOT)),'page':n,'width':p.rect.width,'height':p.rect.height,
           'method':'tesseract-eng' if ocr else 'embedded','text':p.get_text(textpage=tp),
           'words':[list(w[:5]) for w in p.get_text('words',textpage=tp)],
           'blocks':[{'box':list(b[:4]),'text':b[4]} for b in p.get_text('blocks',textpage=tp) if b[6]==0]}
        dump(dest,d)

def extract():
    jobs=[]
    for b in [17,18,19,20]:
        count=len(pymupdf.open(source(b)))
        jobs +=[(b,n) for n in range(1,count+1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        for i,_ in enumerate(pool.map(cache_page,jobs),1):
            if i%25==0:print('cached',i,flush=True)

def page(book,n):
    p=PREP/f'cam{book}'/f'p{n:03}.json'
    if not p.exists():cache_page((book,n))
    return json.loads(p.read_text(encoding='utf8'))

def clean(text):
    text=text.replace('\u00ad','').replace('–','-').replace('—','-')
    lines=text.splitlines()
    out=[]
    for s in lines:
        s=s.strip()
        if re.search(r'ielts.?fighter|Làm đề|Website tự|Tham gia group|facebook.com',s,re.I):continue
        if re.fullmatch(r'(?:Test\s*\d|Listening|LISTENING)',s):continue
        if re.search(r'1718867188|^BE,|^RE,|^BS,|^Fc ve|^ah [ov]e|^hen0|^Dhak|^hea$|^Ara|^Rais|^rene|^Fete|^Eth |^Re [J}\d]|^aps$|^Es$|^Eps|^Bite|^Fia|^\+>|^-\+|^p\.\s*\d|^->|^\+>/|^\w{0,3}\s*p\.\d',s):continue
        out.append(s)
    if out and re.fullmatch(r'\d{1,3}',out[-1]):out.pop()
    return '\n'.join(out).strip()

def audio(book,test,part):
    base=ROOT/'Tài liệu Cambridge'/f'CAMBRIDGE-{book}'
    files=[p for p in base.rglob('*') if p.suffix.lower() in ['.mp3','.m4a'] and not p.name.startswith('._') and '__MACOSX' not in p.parts]
    if book==20:chosen=next(p for p in files if p.name==f'T{test}S{part}.m4a')
    elif book==17:chosen=next((p for p in files if p.name==f'C17T{test}P{part}.mp3'),None)
    else:
        patterns=[rf'(?:test|t)[ _-]*{test}.*(?:part|section|s|p)[ _-]*{part}\b',rf'section[ _-]*{test}.*part[ _-]*{part}\b',rf'C{book}T{test}P{part}\b',rf'T{test}S{part}\b']
        chosen=next((p for p in files if any(re.search(pat,p.stem,re.I) for pat in patterns)),None)
        if not chosen:
            print('audio candidates',book,test,part,[p.name for p in files]);raise ValueError('audio missing')
    if chosen is None:
        dest=PREP/f'cam{book}'/f'cam{book}-test{test}-part{part}.mp3'
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            req=urllib.request.Request(f'https://www.luckyielts.com/wp-content/uploads/2025/07/cambridge-ielts-17-academic-listening-4-audio-{part}.mp3',headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.luckyielts.com/','Range':'bytes=0-'})
            with urllib.request.urlopen(req,timeout=90) as response:dest.write_bytes(response.read())
        chosen=dest
    digest=hashlib.sha256(chosen.read_bytes()).hexdigest()
    dest=LIB/'audio'/(digest+chosen.suffix.lower());dest.parent.mkdir(exist_ok=True)
    if not dest.exists():shutil.copyfile(chosen,dest)
    duration=AudioFile(chosen).info.length
    result={'url':'/library-audio/'+dest.name,'sha256':digest,'duration':round(duration,3),'start':0,'end':round(duration,3),'source':str(chosen.relative_to(ROOT)),
            'verification':{'status':'pending_audio_comparison','sourceTranscript':True}}
    if (book,test)==(20,1):
        result['verification']={'status':'verified','method':'Local PDF audioscript compared with opening and ending ASR samples; original audio preserved','reviewReport':f'library/preparation/listening/cam20/audio-t1-p{part}.json'}
        if part==1:result['start']=56.2;result['end']=461
        if part==4:result['end']=390.5
    return result

def source_image(book,n):
    target=LIB/'assets'/f'l-cam{book}-source-{n:03}.webp'
    if not target.exists():
        with pymupdf.open(source(book)) as d:
            p=d[n-1];clip=p.rect
            if book==17:clip=pymupdf.Rect(0,75,p.rect.width,p.rect.height-30)
            else:clip=pymupdf.Rect(0,35,p.rect.width,p.rect.height-30)
            pix=p.get_pixmap(dpi=150,clip=clip,alpha=False)
            from PIL import Image
            Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(target,quality=90)
    return {'url':'/library-assets/'+target.name,'page':n}

def opts(s):
    matches=list(re.finditer(r'(?m)^([A-J])(?:[.\s_~—-]+|(?=\d))',s))
    return [{'value':m[1],'label':re.sub(r'\s+',' ',s[m.end():matches[i+1].start() if i+1<len(matches) else len(s)]).strip(' _.-')}
            for i,m in enumerate(matches)]

def group_data(book,test,part,lo,hi,body,pages):
    body=body.strip()
    kind='multi' if re.search(r'Choose\s+(?:TWO|THREE)\s+letters',body,re.I) else 'choice' if 'Choose the correct letter' in body else 'matching' if re.search(r'Choose\s+(?:FOUR|FIVE|SIX|SEVEN)|Write the correct letter|write the correct letter',body) else 'completion'
    if kind=='completion' and len(re.findall(r'(?m)^A\.\s',body))>=2:kind='choice'
    m=re.search(r'((?:Write|Choose)\s+(?:NO MORE THAN |ONE |TWO |THREE ).*?for each answer\.)',body,re.I|re.S)
    instruction_end=0
    commands=[]
    for line in body.splitlines():
        if re.search(r'^(?:Complete|Write|Choose|Label)\b',line) or commands and not re.search(r'[.!?]$',commands[-1]):commands.append(line);instruction_end+=len(line)+1
        elif not commands and len(line)<40:instruction_end+=len(line)+1
        else:break
    instructions='\n'.join(commands)
    if kind in ['choice','multi']:
        command_match=re.search(r'(?m)^Choose[^\n]+',body)
        if command_match:
            instructions=command_match.group();instruction_end=command_match.end()
        elif kind=='choice':instructions='Choose the correct letter, A, B or C.';instruction_end=0
    limit_match=re.search(r'(?:NO MORE THAN )?(?:ONE|TWO|THREE) WORDS?(?: ONLY| AND/OR A NUMBER| AND/ORA NUMBER| AND A NUMBER)?',body,re.I)
    wordlimit=limit_match.group().replace('AND/ORA','AND/OR A').upper() if limit_match else None
    group={'id':f'l-cam{book}-t{test}-p{part}-q{lo}-{hi}','type':kind,'heading':f'Questions {lo}–{hi}',
           'instructions':instructions,'body':body,'questions':[],'sourceImages':[source_image(book,n) for n in pages],
           'sourcePages':[{'file':str(source(book).relative_to(ROOT)),'page':n} for n in pages]}
    if wordlimit:
        group['wordLimit']={'ONE':1,'TWO':2,'THREE':3}[re.search(r'ONE|TWO|THREE',wordlimit)[0]]
        group['allowNumber']='NUMBER' in wordlimit
    tail=body[instruction_end:]
    if kind=='multi':
        group['options']=opts(tail)
        group['questions']=[{'number':n,'text':''} for n in range(lo,hi+1)]
        group['body']=re.split(r'(?m)^[A-E][.\s_-]',tail)[0].strip()
        group['choose']=hi-lo+1
    elif kind=='choice':
        starts=list(re.finditer(r'(?m)^\s*(\d{1,2})[.)]?\s*(?=\S)',tail))
        # bare OCR numbers are line-alone; preserve them before prose.
        by={int(m[1]):m for m in starts if lo<=int(m[1])<=hi}
        for n in range(lo,hi+1):
            mm=by.get(n)
            if not mm:group['questions'].append({'number':n,'text':'','options':[]});continue
            end=min([v.start() for k,v in by.items() if k>n]+[len(tail)])
            chunk=tail[mm.end():end]
            om=re.search(r'(?m)^[A-C](?:[.\s_~-]|(?=\d))',chunk)
            group['questions'].append({'number':n,'text':re.sub(r'\s+',' ',chunk[:om.start()] if om else chunk).strip(),'options':opts(chunk)})
        group['body']=''
    elif kind=='matching':
        first_option=re.search(r'(?m)^[A-J](?:[.\s_~—-]+|(?=\d))',body)
        first_question=re.search(rf'(?m)^\s*{lo}[.)]?\s*(?=\S)',body)
        if first_option:
            group['instructions']=re.sub(r'\s+',' ',body[:min(first_option.start(),first_question.start() if first_question else len(body))]).strip()
            if first_question and first_question.start()<first_option.start():
                group['options']=opts(body[first_option.start():]);tail=body[:first_option.start()]
            else:tail=body[first_option.start():];group['options']=opts(tail)
        else:
            group['instructions']=body[:first_question.start() if first_question else len(body)]
            letters=re.search(r'\b([A-Z])\s*[-–—]\s*([A-Z])\b',body)
            group['options']=[{'value':chr(n),'label':chr(n)} for n in range(ord(letters[1]),ord(letters[2])+1)] if letters else []
        firstq=re.search(rf'(?m)^\s*{lo}\b',tail)
        if firstq:
            if first_option and not (first_question and first_question.start()<first_option.start()):group['options']=opts(tail[:firstq.start()])
            qtext=tail[firstq.start():]
            starts=list(re.finditer(r'(?m)^\s*(\d{1,2})[.)]?\s*',qtext))
            for n in range(lo,hi+1):
                mm=next((m for m in starts if int(m[1])==n),None)
                end=next((m.start() for m in starts if mm and m.start()>mm.start()),len(qtext))
                label=re.sub(r'\s+',' ',qtext[mm.end():end] if mm else '').strip()
                label=re.sub(r'[.\s_…]{3,}.*$','',label)
                group['questions'].append({'number':n,'text':label})
        else:group['questions']=[{'number':n,'text':''} for n in range(lo,hi+1)]
        group['body']=''
    else:
        group['questions']=[{'number':n,'text':''} for n in range(lo,hi+1)]
        # Corrected flow content is applied during editorial review below.
        blocks=[]
        content=[];last=0
        pat=re.compile(r'\b('+ '|'.join(str(n) for n in range(lo,hi+1))+r')\s*(?:_{2,}|[.]{3,}|[…]{1,})')
        for mm in pat.finditer(tail):
            content.append(tail[last:mm.start()]);content.append({'number':int(mm[1])});last=mm.end()
        content.append(tail[last:])
        blocks=[{'tag':'p','content':content}]
        if sorted(v['number'] for v in content if isinstance(v,dict))==list(range(lo,hi+1)):
            group['layout']={'kind':'flow','blocks':blocks};group['body']=''
    return group

def verify_audio():
    from faster_whisper import WhisperModel
    import av,numpy as np
    def decode_audio(path):
        resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
        chunks=[]
        with av.open(path) as container:
            for frame in container.decode(audio=0):
                for out in resampler.resample(frame):chunks.append(out.to_ndarray().flatten())
            for out in resampler.resample(None):chunks.append(out.to_ndarray().flatten())
        return np.concatenate(chunks).astype(np.float32)/32768
    model=WhisperModel('tiny.en',device='cpu',compute_type='int8',download_root=str(PREP/'models'),cpu_threads=3,local_files_only=True)
    for book in [20,17,18,19]:
        for test in range(1,5):
            for part in range(1,5):
                report=PREP/f'cam{book}'/f'audio-t{test}-p{part}.json'
                if report.exists():continue
                meta=audio(book,test,part);path=LIB/'audio'/Path(meta['url']).name
                samples=decode_audio(str(path))
                proof={'audio':meta,'model':'faster-whisper tiny.en int8','samples':[]}
                for name,start,end in [('opening',0,min(100,meta['duration'])),('ending',max(0,meta['duration']-65),meta['duration'])]:
                    segments,info=model.transcribe(samples[int(start*16000):int(end*16000)],beam_size=3,language='en',condition_on_previous_text=False)
                    proof['samples'].append({'name':name,'start':start,'end':end,'text':' '.join(s.text.strip() for s in segments)})
                dump(report,proof);print('audio ASR',book,test,part,flush=True)

SOURCES={
 17:[[[3],[4,5],[6,7],[8]],[[24],[25,26],[27,28],[29]],[[46],[47,48],[49,50],[51]],[[68],[69,70],[71,72],[73]]],
 18:[[[12],[13,14],[15,16],[17]],[[34,35],[36,37],[38,39],[40]],[[57],[58,59],[60,61],[62]],[[80],[81,82],[83,84],[85]]],
 19:[[[9],[10,11],[12,13],[14]],[[32,33],[34,35],[36,37],[38]],[[54,55],[56,57],[58,59],[60]],[[77],[78,79],[80,81],[82]]],
 20:[[[1],[1,2,3],[3,4,5],[5,6]],[[22,23],[23,24],[25,26],[26,27]],[[43],[44,45],[45,46],[47]],[[61,62],[62,63],[63,64,65],[65,66]]]
}
KEYS20=[
['fish','roof','Spanish','vegetarian','Audley','hotel','reviews','local','30|thirty','average','A','B','C','A','B','C','A','E','C','E','C','E','A','C','A','B','A','B','A','C','factories','dead','whale','apartments','park','art','beaches','ferry','bikes','drone'],
['break','time','shower','money','memory','lifting','fall','taxi','insurance','stress','D','I','H','E','A','B','B','A','B','A','D','G','B','A','E','C','A','A','B','C','pictures|photos|photographs','vegan','chefs|cooks','journalists|reporters','health','coffee','environment','reputation','price|cost','soil'],
['239','modern','lamp','Aaron','damage','electronic','insurance','space','app','exchanges','B','A','A','C','B','C','B','A','G','E','B','A','C','A','C','B','F','E','B','D','adaptation','cognitive','desks','taps','blue','voice','pregnant','shoulders','police','temperature'],
["Kings|King's",'125','walking','boat','Tuesday','space','vegetarian','2.30|two thirty','75|seventy-five','port','B','B','A','C','D','F','B','H','C','G','C','E','A','C','C','A','A','B','B','C','rats','snakes','tourism','traffic','rain','poison','building','dog','noise','combination']]

def rich(s):
    parts=re.split(r'(\{\d+\})',s)
    return [({'number':int(t[1:-1])} if re.fullmatch(r'\{\d+\}',t) else t) for t in parts if t]

def flow(s):
    return {'kind':'flow','blocks':[{'tag':'h3' if not line.startswith('- ') else 'li','content':rich(line.removeprefix('- '))} for line in s.strip().splitlines() if line.strip()]}

def table(rows):
    return {'kind':'table','rows':[{'cells':[{'content':rich(c),'header':i==0} for c in row]} for i,row in enumerate(rows)]}

FLOWS={
(19,1,1,1):'''Hinchingbrooke Country Park
The park
- Area: {1} hectares
- Habitats: wetland, grassland and woodland
- Wetland: lakes, ponds and a {2}
- Wildlife includes birds, insects and animals
Subjects studied in educational visits include
- Science: Children look at {3} about plants, etc.
- Geography: includes learning to use a {4} and compass
- History: changes in land use
- Leisure and tourism: mostly concentrates on the park's {5}
- Music: Children make {6} with natural materials, and experiment with rhythm and speed.
Benefits of outdoor educational visits
- They give children a feeling of {7} that they may not have elsewhere.
- Children learn new {8} and gain self-confidence.
Practical issues
- Cost per child: £ {9}
- Adults, such as {10}, free''',
(19,1,4,31):'''Céide Fields
- an important Neolithic archaeological site in the northwest of Ireland
Discovery
- In the 1930s, a local teacher realised that stones beneath the bog surface were once {31}.
- His {32} became an archaeologist and undertook an investigation of the site:
- a traditional method used by local people to dig for {33} was used to identify where stones were located
- carbon dating later proved the site was Neolithic.
- Items are well preserved in the bog because of a lack of {34}.
Neolithic farmers
- Houses were {35} in shape and had a hole in the roof.
- Neolithic innovations include:
- cooking indoors
- pots used for storage and to make {36}.
- Each field at Céide was large enough to support a big {37}.
- The fields were probably used to restrict the grazing of animals - no evidence of structures to house them during {38}.
Reasons for the decline in farming
- a decline in {39} quality
- an increase in {40}''',
(19,2,1,1):'''Guitar Group
- Coordinator: Gary {1}
- Level: {2}
Place:
- the {3}
- {4} Street
- First floor, Room T347
- Time: Thursday morning at {5}
- Recommended website: ‘The perfect {6}’''',
(19,2,4,31):'''Tardigrades
- more than 1,000 species, 0.05–1.2 millimetres long
- also known as water ‘bears’ (due to how they {31}) and ‘moss piglets’
Physical appearance
- a {32} round body and four pairs of legs
- claws or {33} for gripping
- absence of respiratory organs
- body filled with a liquid that carries both {34} and blood
- mouth shaped like a {35} with teeth called stylets
Habitat
- often found at the bottom of a lake or on plants
- very resilient and can exist in very low or high {36}
Cryptobiosis
- In dry conditions, they roll into a ball called a ‘tun’.
- They stay alive with a much lower metabolism than usual.
- A type of {37} ensures their DNA is not damaged.
- Research is underway to find out how many days they can stay alive in {38}.
Feeding
- consume liquids, e.g., those found in moss or {39}
- may eat other tardigrades
Conservation status
- They are not considered to be {40}.''',
(19,3,1,1):'''Local food shops
Where to go
- Kite Place - near the {1}
Fish market
- cross the {2} and turn right
- best to go before {3} pm, earlier than closing time
Organic shop
- called {4}
- below a restaurant in the large, grey building
- look for the large {5} outside
Supermarket
- take a {6} minibus, number 289''',
(19,3,4,31):'''Microplastics
Where microplastics come from
- fibres from some {31} during washing
- the breakdown of large pieces of plastic
- waste from industry
- the action of vehicle tyres on roads
Effects of microplastics
- They cause injuries to the {32} of wildlife and affect their digestive systems.
- They enter the food chain, e.g., in bottled and tap water, {33} and seafood.
- They may not affect human health, but they are already banned in skin cleaning products and {34} in some countries.
- Microplastics enter the soil through the air, rain and {35}.
Microplastics in the soil - a study by Anglia Ruskin University
- Earthworms are important because they add {36} to the soil.
- The study aimed to find whether microplastics in earthworms affect the {37} of plants.
The study found that microplastics caused:
- {38} loss in earthworms
- fewer seeds to germinate
- a rise in the level of {39} in the soil.
The study concluded:
- soil should be seen as an important natural process.
- changes to soil damage both ecosystems and {40}.''',
(19,4,1,1):'''First day at work
- Name of supervisor: {1}
- Where to leave coat and bag: use {2} in staffroom
See Tiffany in HR:
- to give {3} number
- to collect {4}
- Location of HR office: on {5} floor
- Supervisor's mobile number: {6}''',
(19,4,4,31):'''Tree planting
Reforestation projects should:
- include a range of tree species
- not include invasive species because of possible {31} with native species
- aim to capture carbon, protect the environment and provide sustainable sources of {32} for local people
- use tree seeds with a high genetic diversity to increase resistance to {33} and climate change
- plant trees on previously forested land which is in a bad condition, not select land which is being used for {34}
Large-scale reforestation projects
- Base planning decisions on information from accurate {35}.
- Drones are useful for identifying areas in Brazil which are endangered by keeping {36} and illegal logging.
Lampang Province, Northern Thailand
- A forest was restored in an area damaged by mining.
- A variety of native fig trees were planted, which are important for
- supporting many wildlife species
- increasing the {37} of recovery by attracting animals and birds, e.g., {38} were soon attracted to the area.
Involving local communities
- Destruction of mangrove forests in Madagascar made it difficult for people to make a living from {39}.
The mangrove reforestation project:
- provided employment for local people
- restored a healthy ecosystem
- protects against the higher risk of {40}.''',
(18,1,1,1):'''Transport survey
- Name: Sadie Jones
- Year of birth: 1991
- Postcode: {1}
Travelling by bus
- Date of bus journey: {2}
- Reason for trip: shopping and visit to the {3}
- Travelled by bus because cost of {4} too high
- Got on bus at {5} Street
Complaints about bus service:
- bus today was {6}
- frequency of buses in the {7}
Travelling by car
- Goes to the {8} by car
Travelling by bicycle
- Dislikes travelling by bike in the city centre because of the {9}
- Doesn't own a bike because of a lack of {10}''',
(18,1,4,31):'''Elephant translocation
Reasons for overpopulation at Majete National Park
- strict enforcement of anti-poaching laws
- successful breeding
Problems caused by elephant overpopulation
- greater competition, causing hunger for elephants
- damage to {31} in the park
The translocation process
- a suitable group of elephants from the same {32} was selected
- vets and park staff made use of {33} to help guide the elephants into an open plain
- elephants were immobilised with tranquilisers
- this process had to be completed quickly to reduce {34}
- elephants had to be turned on their {35} to avoid damage to their lungs
- elephants' {36} had to be monitored constantly
- tracking devices were fitted to the matriarchs
- data including the size of their tusks and {37} was taken
- elephants were taken by truck to their new reserve
Advantages of translocation at Nkhotakota Wildlife Park
- {38} opportunities
- a reduction in the number of poachers and {39}
- an example of conservation that other parks can follow
- an increase in {40} as a contributor to GDP''',
(18,2,1,1):'''Working at Milo's Restaurants
Benefits
- {1} provided for all staff
- {2} during weekdays at all Milo's Restaurants
- {3} provided after midnight
Person specification
- must be prepared to work well in a team
- must care about maintaining a high standard of {4}
- must have a qualification in {5}''',
(18,2,4,31):'''Pockets
Reason for choice of subject
- They are {31} but can be overlooked by consumers and designers.
Pockets in men's clothes
- Men started to wear {32} in the 18th century.
- A {33} sewed pockets into the lining of the garments.
- The wearer could use the pockets for small items.
- Bigger pockets might be made for men who belonged to a certain type of {34}.
Pockets in women's clothes
- Women's pockets were less {35} than men's.
- Women were very concerned about pickpockets.
- Pockets were produced in pairs using {36} to link them together.
- Pockets hung from the women's {37} under skirts and petticoats.
- Items such as {38} could be reached through a gap in the material.
- Pockets, of various sizes, stayed inside clothing for many decades.
- When dresses changed shape, hidden pockets had a negative effect on the {39} of women.
- Bags called ‘pouches’ became popular, before women carried a {40}.''',
(18,3,1,1):'''Wayside Camera Club membership form
- Name: Dan Green
- Email address: dan1068@market.com
- Home address: 52 {1} Street, Peacetown
- Heard about us: from a {2}
Reasons for joining:
- to enter competitions
- to {3}
- Type of membership: {4} membership (£30)''',
(18,3,4,31):'''Space Traffic Management
A Space Traffic Management system
- is a concept similar to Air Traffic Control, but for satellites rather than planes.
- would aim to set up legal and {31} ways of improving safety.
- does not actually exist at present.
Problems in developing effective Space Traffic Management
- Satellites are now quite {32} and therefore more widespread (e.g. there are constellations made up of {33} of satellites).
- At present, satellites are not required to transmit information to help with their {34}.
- There are few systems for {35} satellites.
- Small pieces of debris may be difficult to identify.
- Operators may be unwilling to share details of satellites used for {36} or commercial reasons.
- It may be hard to collect details of the object's {37} at a given time.
- Scientists can only make a {38} about where the satellite will go.
Solutions
- Common standards should be agreed on for the presentation of information.
- The information should be combined in one {39}.
- A coordinated system must be designed to create {40} in its users.''',
(18,4,1,1):'''Job details from employment agency
Role
- {1}
Location
- Fordham {2} Centre
- {3} Road, Fordham
Work involves
- dealing with enquiries
- making {4} and reorganising them
- maintaining the internal {5}
- general administration
Requirements
- {6} (essential)
- a calm and {7} manner
- good IT skills
Other information
- a {8} job - further opportunities may be available
- hours: 7.45 a.m. to {9} p.m. Monday to Friday
- {10} is available onsite''',
(18,4,4,31):'''Victor Hugo
His novel, Les Misérables
- It has been adapted for theatre and cinema.
- We know more about its overall {31} than about its author.
His early career
- In Paris, his career was successful and he led the Romantic movement.
- He spoke publicly about social issues, such as {32} and education.
- Napoleon III disliked his views and exiled him.
His exile from France
- Victor Hugo had to live elsewhere in {33}.
- He used his income from the sale of some {34} he had written to buy a house on Guernsey.
His house on Guernsey
- Victor Hugo lived in this house until the end of the Empire in France.
- The ground floor contains portraits, {35} and tapestries that he valued.
- He bought cheap {36} made of wood and turned this into beautiful wall carvings.
- The first floor consists of furnished areas with wallpaper and {37} that have a Chinese design.
- The library still contains many of his favourite books.
- He wrote in a room at the top of the house that had a view of the {38}.
- He entertained other writers as well as poor {39} in his house.
- Victor Hugo's {40} gave ownership of the house to the city of Paris in 1927.''',
(17,1,1,1):'''Buckworth Conservation Group
Regular activities
Beach
- making sure the beach does not have {1} on it
- no {2}
Nature reserve
- maintaining paths
- nesting boxes for birds installed
- next task is taking action to attract {3} to the place
- identifying types of {4}
- building a new {5}
Forthcoming events
Saturday
- meet at Dunsmore Beach car park
- walk across the sands and reach the {6}
- take a picnic
- wear appropriate {7}
Woodwork session
- suitable for {8} to participate in
- making {9} out of wood
- 17th, from 10 a.m. to 3 p.m.
- cost of session (no camping): £ {10}''',
(17,1,4,31):'''Labyrinths
Definition
- a winding spiral path leading to a central area
Labyrinths compared with mazes
- Mazes are a type of {31}
- {32} is needed to navigate through a maze
- the word ‘maze’ is derived from a word meaning a feeling of {33}
- Labyrinths represent a journey through life
- they have frequently been used in {34} and prayer
Early examples of the labyrinth spiral
- Ancient carvings on {35} have been found across many cultures
- The Pima, a Native American tribe, wove the symbol on baskets
- Ancient Greeks used the symbol on {36}
Walking labyrinths
- The largest surviving example of a turf labyrinth once had a big {37} at its centre
Labyrinths nowadays
- Believed to have a beneficial impact on mental and physical health, e.g., walking a maze can reduce a person's {38} rate
- Used in medical and health and fitness settings and also prisons
- Popular with patients, visitors and staff in hospitals
- patients who can't walk can use ‘finger labyrinths’ made from {39}
- research has shown that Alzheimer's sufferers experience less {40}''',
(17,2,1,1):'''Opportunities for voluntary work in Southoe village
Library
- Help with {1} books (times to be arranged)
- Help needed to keep {2} of books up to date
- Library is in the {3} Room in the village hall
Lunch club
- Help by providing {4}
- Help with hobbies such as {5}
Help for individuals needed next week
- Taking Mrs Carroll to {6}
- Work in the {7} at Mr Selsbury's house''',
(17,2,4,31):'''The impact of digital technology on the Icelandic language
The Icelandic language
- has approximately {31} speakers
- has a {32} that is still growing
- has not changed a lot over the last thousand years
- has its own words for computer-based concepts, such as web browser and {33}
Young speakers
- are big users of digital technology, such as {34}
- are becoming {35} very quickly
- are having discussions using only English while they are in the {36} at school
- are better able to identify the content of a {37} in English than Icelandic
Technology and internet companies
- write very little in Icelandic because of the small number of speakers and because of how complicated its {38} is
The Icelandic government
- has set up a fund to support the production of more digital content in the language
- believes that Icelandic has a secure future
- is worried that young Icelanders may lose their {39} as Icelanders
- is worried about the consequences of children not being {40} in either Icelandic or English''',
(17,3,1,1):'''Advice on surfing holidays
Jack's advice
- Recommends surfing for {1} holidays in the summer
- Need to be quite {2}
Irish surfing locations
County Clare
- Lahinch has some good quality {3} and surf schools
- There are famous cliffs nearby
County Mayo
- Good surf school at {4} beach
- Surf camp lasts for one {5}
- Can also explore the local {6} by kayak
Weather
- Best month to go: {7}
- Average temperature in summer: approx. {8} degrees
Costs
Equipment
- Wetsuit and surfboard: {9} euros per day
- Also advisable to hire {10} for warmth''',
(17,3,4,31):'''Bird Migration Theory
Most birds are believed to migrate seasonally.
Hibernation theory
- It was believed that birds hibernated underwater or buried themselves in {31}.
- This theory was later disproved by experiments on caged birds.
Transmutation theory
- Aristotle believed birds changed from one species into another in summer and winter.
- In autumn he observed that redstarts experience the loss of {32} and thought they then turned into robins.
- Aristotle's assumptions were logical because the two species of birds had a similar {33}.
17th century
- Charles Morton popularised the idea that birds fly to the {34} in winter.
Scientific developments
- In 1822, a stork was killed in Germany which had an African spear in its {35}.
- previously there had been no {36} that storks migrate to Africa
- Little was known about the {37} and journeys of migrating birds until the practice of ringing was established.
- It was thought large birds carried small birds on some journeys because they were considered incapable of travelling across huge {38}.
- Ringing depended on what is called the {39} of dead birds.
- In 1931, the first {40} to show the migration of European birds was printed.''',
(17,4,1,1):'''Easy Life Cleaning Services
Basic cleaning package offered
- Cleaning all surfaces
- Cleaning the {1} throughout the apartment
- Cleaning shower, sinks, toilet etc.
Additional services agreed
Every week
- Cleaning the {2}
- Ironing clothes - {3} only
Every month
- Cleaning all the {4} from the inside
- Washing down the {5}
Other possibilities
- They can organise a plumber or an {6} if necessary.
- A special cleaning service is available for customers who are allergic to {7}.
Information on the cleaners
- Before being hired, all cleaners have a background check carried out by the {8}.
- References are required.
- All cleaners are given {9} for two weeks.
- Customers send a {10} after each visit.
- Usually, each customer has one regular cleaner.''',
(17,4,4,31):'''Maple syrup
What is maple syrup?
- made from the sap of the maple tree
- colour described as {31}
- added to food or used in cooking
- very {32} compared to refined sugar
The maple tree
- has many species
- needs sunny days and cool nights
- maple leaf has been on the Canadian flag since 1964
- needs moist soil but does not need fertiliser as well
- best growing conditions and {33} are in Canada and North America
Early maple sugar producers
- made holes in the tree trunks
- used hot {34} to heat the sap
- used tree bark to make containers for collection
- sweetened food and drink with sugar
Today's maple syrup
The trees
- Tree trunks may not have the correct {35} until they have been growing for 40 years.
- The changing temperature and movement of water within the tree produces the sap.
The production
- A tap is drilled into the trunk and a {36} carries the sap into a bucket.
- Large pans of sap called evaporators are heated by means of a {37}.
- A lot of {38} is produced during the evaporation process.
- ‘Sugar sand’ is removed because it makes the syrup look {39} and affects the taste.
- The syrup is ready for use.
- A huge quantity of sap is needed to make a {40} of maple syrup.''',
}
KEYS17=[
['litter','dogs','insects','butterflies','wall','island','boots','beginners','spoons','35|thirty five','A','C','B','B','A','D','B','C','D','E','A','B','B','A','C','C','A','E','F','C','puzzle','logic','confusion','meditation','stone','coins','tree','breathing','paper','anxiety'],
['collecting','records','West','transport','art','hospital','garden','quiz','tickets','poster','B','C','C','B','D','C','G','A','E','F','D','E','D','C','A','E','F','B','C','C','321,000|321000','vocabulary','podcast','smartphones','bilingual','playground','picture','grammar','identity','fluent'],
['family','fit','hotels','Carrowniskey','week','bay','September','19|nineteen','30|thirty','boots','B','E','C','C','A','E','D','G','F','C','B','A','A','B','C','A','D','B','F','H','mud','feathers','shape','moon','neck','evidence','destinations','oceans','recovery','atlas'],
['floor|floors','fridge','shirts','windows','balcony','electrician','dust','police','training','review','A','A','A','C','A','C','B','C','B','A','C','E','A','D','B','F','A','D','C','G','golden','healthy','climate','rock|rocks','diameter','tube','fire','steam','cloudy','litre|liter']]
KEYS18=[
['DW30 7YZ|DW307YZ','24 April|24th April','dentist','parking','Claxby','late','evening','supermarket','pollution','storage','C','A','A','B','E','B','G','D','A','F','A','B','A','C','B','A','B','E','A','C','fences','family','helicopters','stress','sides','breathing','feet','employment','weapons','tourism'],
['training','discount','taxi','service','English','Wivenhoe','equipment','9.75','deliveries','Sunday','B','E','B','C','G','C','D','B','H','A','C','A','B','B','A','B','D','A','C','F','convenient','suits','tailor','profession','visible','string|strings','waist|waists','perfume','image','handbag'],
['Marrowfield','relative','socialise|socialize','full','Domestic Life','clouds','timing','Animal Magic','movement|animal movement','dark','B','C','B','D','C','B','B','C','A','A','A','E','B','D','G','E','B','C','F','A','technical','cheap','thousands','identification','tracking','military','location','prediction','database','trust'],
['receptionist','Medical','Chastons','appointments','database','experience','confident','temporary','1.15','parking','B','A','A','C','F','G','E','A','C','B','B','D','D','A','C','G','F','A','B','C','plot','poverty','Europe','poetry','drawings','furniture','lamps','harbour|harbor','children','relatives']]
KEYS19=[
['69|sixty-nine','stream','data','map','visitors','sounds','freedom','skills','4.95','leaders','B','A','B','C','A','G','C','B','D','A','B','D','A','E','D','G','C','B','F','H','walls','son','fuel','oxygen','rectangular','lamps','family','winter','soil','rain'],
['Mathieson','beginners','college','New','11|eleven|11 am|eleven am','instrument','ear','clapping','recording','alone','A','B','A','B','C','A','C','E','A','B','A','B','B','B','E','B','A','C','C','A','move','short','discs','oxygen','tube','temperatures','protein','space','seaweed','endangered'],
['harbour|harbor','bridge','3.30|three thirty|½|half 3|three','Rose','sign','purple','samphire','melon','coconut','strawberry','C','D','F','G','B','H','D','E','B','C','C','B','A','A','C','C','H','E','B','F','clothing','mouths','salt','toothpaste','fertilisers|fertilizers','nutrients','growth','weight','acid','society'],
['Kaeden','locker|lockers','passport','uniform','third|3rd','0412 665 903|0412665903','yellow','plastic','ice','gloves','C','E','A','D','A','B','C','A','C','B','A','C','A','B','C','D','F','A','C','G','competition','food','disease','agriculture','maps','cattle','speed','monkeys','fishing','flooding']]

def editorial(obj):
    book,test=obj['book'],obj['test']
    for p in obj['parts']:
        for g in p['groups']:
            key=(book,test,p['number'],g['questions'][0]['number'])
            if key in FLOWS:g['layout']=flow(FLOWS[key]);g['body']=''
    if (book,test)==(17,2):
        g=obj['parts'][0]['groups'][1]
        g['layout']=table([['Date','Event','Location','Help needed'],['19 Oct','{8}','Village hall','providing refreshments'],['18 Nov','dance','','checking {9}'],['31 Dec',"New Year's Eve party",'Mountfort Hotel','designing the {10}']]);g['layout']['caption']='Village social events';g['body']=''
    if (book,test)==(18,2):
        g=obj['parts'][0]['groups'][1]
        g['layout']=table([['Location','Job title','Responsibilities include','Pay and conditions'],['{6} Street','Breakfast supervisor','Checking portions, etc. are correct\n\nMaking sure {7} is clean','Starting salary £ {8} per hour\n\nStart work at 5.30 a.m.'],['City Road','Junior chef','Supporting senior chefs\n\nMaintaining stock and organising {9}','Annual salary £23,000\n\nNo work on a {10} once a month']]);g['body']=''
    if (book,test)==(18,3):
        g=obj['parts'][0]['groups'][1]
        g['layout']=table([['Title of competition','Instructions','Feedback to Dan'],["‘{5}’",'A scene in the home',"The picture's composition was not good."],["‘Beautiful Sunsets’",'Scene must show some {6}','The {7} was wrong.'],["‘{8}’",'Scene must show {9}','The photograph was too {10}.']]);g['layout']['caption']='Photography competitions';g['body']=''
    if (book,test)==(19,2):
        g=obj['parts'][0]['groups'][1]
        g['layout']=table([['Time','Activity','Notes'],['5 minutes','tuning guitars','using an app or by {7}'],['10 minutes','strumming chords using our thumbs','keeping time while the teacher is {8}'],['15 minutes','playing songs','often listening to a {9} of a song'],['10 minutes','playing single notes and simple tunes','playing together, then {10}'],['5 minutes','noting things to practise at home','']]);g['layout']['caption']='A typical 45-minute guitar lesson';g['body']=''
    if (book,test)==(19,3):
        g=obj['parts'][0]['groups'][1]
        g['layout']=table([['','To buy','Other ideas'],['Fish market','a dozen prawns','a handful of {7} (type of seaweed)'],['Organic shop','beans and a {8} for dessert','spices and {9}'],['Bakery','a brown loaf','a {10} tart']]);g['layout']['caption']='Shopping';g['body']=''
    if (book,test)==(19,4):
        g=obj['parts'][0]['groups'][1]
        g['layout']=table([['','Task 1','Task 2','Notes'],['Bakery section','Check sell-by dates','Change price labels','Use {7} labels'],['Sushi takeaway counter','Re-stock with {8} boxes if needed','Wipe preparation area and clean the sink','Do not clean any knives'],['Meat and fish counters','Clean the serving area, including the weighing scales','Collect {9} for the fish from the cold-room','Must wear special {10}']]);g['layout']['caption']='Responsibilities';g['body']=''
    if (book,test)==(20,3):
        g=obj['parts'][0]['groups'][0]
        g['layout']=table([['Name of companies','Information about costs','Additional notes'],['Peak Rentals','Prices range from 105 dollars to {1} dollars per room per month','The furniture is very {2}.\nDelivers in 1–2 days.\nSpecial offer: free {3} with every living room set'],['{4} and Oliver','Mid-range prices\n12% monthly fee for {5}','Also offers a cleaning service'],['Larch Furniture','Offers cheapest prices for renting furniture and {6} items','Must have own {7}.\nMinimum contract length: six months'],['{8} Rentals','See the {9} for the most up-to-date prices','{10} are allowed within 7 days of delivery']]);g['layout']['caption']='Furniture rental companies';g['body']=''
    if (book,test)==(20,1):
        obj['verification']['status']='verified'
        obj['verification']['note']='Questions, table, options, limits and 40 answer keys compared against both locally supplied retyped PDFs; four audio opening/ending samples match local audioscript. Paper transfer directions excluded through audio start/end.'
        group=obj['parts'][0]['groups'][0]
        group['layout']=table([
            ['Name of restaurants','Location','Reason for recommendation','Other comments'],
            ['The junction','Greyson Street, near the station','Good for people who are especially keen on {1}','Quite expensive\n\nThe {2} is a good place for a drink'],
            ['Paloma','In Bow Street next to the cinema','{3} food, good for sharing','Staff are very friendly\n\nNeed to pay 50 deposit\n\nA limited section of {4} on the menu'],
            ['The {5}','At the top of a {6}','A famous chef\n\nAll the {7} are very good\n\nOnly uses {8} ingredients','Set lunch cost: {9} per person\n\nProportions probably of {10} size']])
        group['body']=''
        group=obj['parts'][3]['groups'][0]
        group['layout']=flow('''Reclaiming urban rivers
Historical background
- Nearly all major cities were built on a river.
- Rivers were traditionally used by city dwellers for transport, fishing and recreation.
- Industrial development and rising populations later led to:
- more sewage from houses being discharged into the river
- pollution from {31} on the river bank.
- In 1957, the River Thames in London was declared biologically {32}.
Recent improvements
- Seals and even a {33} have been seen in the River Thames.
- Riverside warehouses are converted to restaurants and {34}.
- In Los Angeles, there are plans to:
- build a riverside {35}.
- display {36} projects.
- In Paris, {37} are created on the sides of the river every summer.
Transport possibilities
- Over 2 billion passengers already travel by {38}.
- Changes in shopping habits mean the number of deliveries that are made is increasing.
- Instead of road transport, goods could be transported by large freight barges and electric {39}, or in the future, by {40}.''')
        group['body']=''
    return obj

def part_text(book,test,part):
    pages=SOURCES[book][test-1][part-1]
    text='\n'.join(clean(page(book,n)['text']) for n in pages)
    if book==20 and (test,part)==(1,2):text=text.replace('Questions 11-13','Questions 11-16')
    mm=re.search(rf'(?m)^PART\s*{part}\b',text)
    if mm:text=text[mm.end():]
    # Shared pages in retyped Cambridge20 contain the next part / reading.
    end=re.search(r'(?m)^PART\s*[1-4]\b|^Reading\s*$|^READING\s*$|^Pasage\s*1\b|^READING PASSAGE',text)
    if end:text=text[:end.start()]
    return text

def transcript_parts(book):
    ranges={17:(89,111),18:(101,120),19:(98,118),20:(81,125)}
    start,end=ranges[book]
    text='\n'.join(clean(page(book,n)['text']) for n in range(start,end+1))
    matches=list(re.finditer(r'(?m)^PART\s*([1-4])\s*$',text))
    result={}
    for i,m in enumerate(matches):
        test=i//4+1;part=int(m[1])
        content=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
        content=re.sub(r'(?m)^TEST\s*\d+\s*$','',content)
        content=re.sub(r'(?m)^Q\d+(?:[/–-]\d+)?\s*$','',content)
        result[(test,part)]=content.strip()
    if len(result)!=16:print('WARNING transcript boundaries',book,len(matches),[(m[1],text[m.end():m.end()+35]) for m in matches])
    return result

def assemble(books=(20,17,18,19)):
    issues=[]
    for book in books:
        transcripts=transcript_parts(book)
        for test in range(1,5):
            obj={'id':f'cam{book}-listening-test{test}','skill':'listening','book':book,'test':test,'title':f'Cambridge {book} · Listening Test {test}',
                 'version':'2026-10-21.listening1','verification':{'status':'review_required','reviewReport':f'library/preparation/listening/cam{book}/editorial-review.json'},'parts':[]}
            for part in range(1,5):
                text=part_text(book,test,part)
                heads=list(re.finditer(r'(?m)^[ :–-]*Questions?\s+(\d+)\s*(?:-|and)\s*(\d+)\s*$',text,re.I))
                groups=[]
                for i,m in enumerate(heads):
                    lo,hi=int(m[1]),int(m[2]);body=text[m.end():heads[i+1].start() if i+1<len(heads) else len(text)].strip(' -\n')
                    if not re.search(r'Complete|Choose|Write|What|Which|Label',body,re.I):continue
                    if lo<part*10-9 or hi>part*10:continue
                    if i+1<len(heads) and lo<int(heads[i+1][1])<=hi:hi=int(heads[i+1][1])-1
                    group=group_data(book,test,part,lo,hi,body,SOURCES[book][test-1][part-1]);groups.append(group)
                nums=[q['number'] for g in groups for q in g['questions']]
                if nums!=list(range(part*10-9,part*10+1)):issues.append([book,test,part,'numbers',nums])
                for g in groups:
                    if g['type']=='completion' and not g.get('layout'):issues.append([book,test,part,g['id'],'flow_missing'])
                    if g['type'] in ['choice','matching','multi']:
                        if g['type']=='choice' and any(len(q['options'])!=3 for q in g['questions']):issues.append([book,test,part,g['id'],'choice_options'])
                        if g['type'] in ['matching','multi'] and not g.get('options'):issues.append([book,test,part,g['id'],'options'])
                obj['parts'].append({'id':f'l-cam{book}-t{test}-p{part}','number':part,'title':f'Part {part}','paragraphs':[],
                    'groups':groups,'sourceImages':[source_image(book,n) for n in SOURCES[book][test-1][part-1]],
                    'sourcePages':[{'file':str(source(book).relative_to(ROOT)),'page':n} for n in SOURCES[book][test-1][part-1]],
                    'audio':audio(book,test,part)})
            editorial(obj)
            dump(LIB/'listening'/'tests'/(obj['id']+'.json'),obj)
            dump(LIB/'listening'/'transcripts'/(obj['id']+'.json'),{'parts':{str(p):transcripts.get((test,p),'') for p in range(1,5)}})
            if book in [17,18,19,20]:
                rawkeys={17:KEYS17,18:KEYS18,19:KEYS19,20:KEYS20}[book][test-1]
                keys={'answers':{str(i+1):a.split('|') for i,a in enumerate(rawkeys)},'multi':[]}
                for p in obj['parts']:
                    for g in p['groups']:
                        if g['type']=='multi':keys['multi'].append({'numbers':[q['number'] for q in g['questions']], 'answers':[rawkeys[q['number']-1] for q in g['questions']]})
                dump(LIB/'listening'/'keys'/(obj['id']+'.json'),keys)
    dump(PREP/'assemble-17-20-issues.json',issues)
    print('issues',len(issues),json.dumps(issues,ensure_ascii=False),flush=True)

if __name__=='__main__':
    if '--extract' in sys.argv:extract()
    if '--audio' in sys.argv:verify_audio()
    if '--assemble' in sys.argv:assemble()
    if '--repair-cache' in sys.argv:
        for b,ns in [(20,range(126,130)),(19,[106,109,113,115])]:
            for n in ns:
                (PREP/f'cam{b}'/f'p{n:03}.json').unlink(missing_ok=True)
                cache_page((b,n));print('repaired',b,n,flush=True)
