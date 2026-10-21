"""Editorial corrections verified against the owner's local Cambridge PDFs.

Run after preparation/assemble. Full reviewed JSON overrides preserve editorial
changes on subsequent imports; this helper records the individual corrections.
"""
from pathlib import Path
import json
import re
import importlib.util

ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/'library'
spec=importlib.util.spec_from_file_location('prepare_library',ROOT/'scripts'/'prepare_library.py')
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
COMMON={
    'ofwhy':'of why','ofmovement':'of movement','ofmoving':'of moving',
    'ofphysical':'of physical','ofthem':'of them','ofpsychological':'of psychological',
    'ofpower':'of power','oftwo':'of two','ofteasers':'of teasers','ofyoung':'of young',
    'ofusers':'of users','halfmillion':'half million','wasa':'was a',
    'becomea':'become a','ifWhaley':'if Whaley','ofthem':'of them',
    'ofstring':'of string','ofoptions':'of options','ofyears':'of years',
    'ofsociety':'of society','oforiginal':'of original','ofpages':'of pages',
    'offive':'of five','ofcomputer':'of computer','ofartificial':'of artificial',
    'oflong':'of long','ofdeaths':'of deaths','ofexploiting':'of exploiting',
    'ofextraction':'of extraction','ofconverted':'of converted','ofurbanism':'of urbanism',
    'ofnew':'of new','ofworth':'of worth','wasa':'was a',
}
CORRECTIONS={
    'cam15-test1':{
        'Myristicafragrans':'Myristica fragrans','rmnning':'running','23m long':'2–3cm long',
        'theynever':'they never','the world, The Dutch':'the world. The Dutch',
        'and. deadly':'and deadly','have it, Nutmeg':'have it. Nutmeg','haif':'half',
        'Sn Lanka':'Sri Lanka','smailer':'smaller','difficuities':'difficulties',
    },
    'cam15-test2':{
        'Atlanta, According':'Atlanta. According','bumed':'burned',
        'de- extinction':'de-extinction','mammoth- like':'mammoth-like',
        'Thefindings':'The findings','letter “e’':'letter ‘e’',
    },
    'cam15-test3':{
        'Mayan” sculpture':'Mayan* sculpture','armed at niche':'aimed at niche',
        'middle- income':'middle-income','wolfruns':'wolf runs',
        'survival- relevant':'survival-relevant','folklorists”':'folklorists*',
        'The Wolfand the Kids':'The Wolf and the Kids',
    },
    'cam15-test4':{
        'the Jand':'the land','local! families':'local families',
        'plant life.“':'plant life.','survive-today':'survive today',
        'shareholders ate under':'shareholders are under','40,000m?':'40,000m³',
        'ptactices':'practices','a Some readers':'Some readers',
    },
    'cam18-test1':{
        'ofyoung':'of young','arounda':'around a','ofpipes':'of pipes',
        'consuminga':'consuming a','upa lot':'up a lot','Atree':'A tree',
        'ofhighest':'of highest','stand”':'stand*','unlessa':'unless a',
        '‘ want to make':'‘I want to make',
    },
    'cam18-test2':{
        'undertakinga':'undertaking a','amore communal':'a more communal',
        'Celtic”':'Celtic**','Powertul':'Powerful','chess- playing':'chess-playing',
        'so- called':'so-called','doa lot':'do a lot','sucha future':'such a future',
        'Vinci’ ideal':'Vinci’s ideal','causeda':'caused a','Georges-Eugéne':'Georges-Eugène',
    },
    'cam18-test3':{
        'Apossible':'A possible','Mannstrém':'Mannström','arise in demand':'a rise in demand',
        'Ifthey':'If they','Evenas':'Even as','cars. . The':'cars. The','ifnot':'if not',
        'Asa teacher':'As a teacher','Ifwe':'If we','Ata macro':'At a macro',
        'The . ; ar ; oy practice':'The practice','and ca: comprehensive':'and comprehensive',
        '‘stream’ ; on ar : of general':'‘stream’ of general',
        'subject- specific':'subject-specific',
        'And that secatag evervous on the sane hike-— regardless orcing every of aptitude — would be madness.':'And that forcing everyone on the same hike — regardless of aptitude — would be madness.',
        'significantly ’ —and negatively':'significantly — and negatively',
        'more- knowledgeable':'more-knowledgeable','Havinga':'Having a',
    },
    'cam18-test4':{
        'InNorth':'In North','providea':'provide a','growa':'grow a','have - also':'have also',
        'be-delivered':'be delivered','probablya':'probably a','When started writing':'When I started writing',
        'paleoclimatology’,':'paleoclimatology*,','and thus have been':'and thus I have been',
        'though certainly have devoted':'though I certainly have devoted',
        'later. have tried':'later. I have tried','In this respect urge':'In this respect I urge',
        'am firmly of the opinion':'I am firmly of the opinion','as think you':'as I think you','bea sufficient':'be a sufficient',
    },
    'cam19-test1':{
        'Gongalo':'Gonçalo','commandof':'command of','knowledgeofthe':'knowledge of the',
        'caravels’':'caravels*','well- known':'well-known','/liad':'Iliad',
        'industries, But':'industries. But','Ist century':'1st century',
        'among, others':'among others','affect attitudes,':'affect attitudes.',
    },
    'cam19-test2':{
        'whena':'when a','Itisn’\'t':'It isn’t','createa':'create a',
        'oneofthose':'one of those','Prof Deborah — Eyre':'Prof Deborah Eyre',
        'on the — book':'on the book','ProfAnders':'Prof Anders','fiom':'from',
        'Did he think — he':'Did he think he','makesa':'makes a','it is character.”':'it is character.’',
    },
    'cam19-test3':{
        'year, These':'year. These','WWEN':'WWFN','Manyofthose':'Many of those',
        'peat’.':'peat*.','Climate- smart':'Climate-smart','CO»':'CO₂',
        '* peal:':'* peat:','CO and methane':'CO₂ and methane','subsidence™’':'subsidence**',
        'stuffof':'stuff of','Hitchhikers Guide':'Hitchhiker’s Guide','voice- morphing':'voice-morphing',
    },
    'cam19-test4':{
        'answeris':'answer is','deep- sea':'deep-sea','drawing, a seawater':'drawing a seawater',
        '*de-watered’':'‘de-watered’','/Kung':'!Kung','happened to us. believe':'happened to us. I believe',
    },
}
SPLITS={
    ('cam15-test1',1):['Always in danger of competition'],
    ('cam15-test1',3):['Thomas Hardy set some of his novels'],
    ('cam15-test2',3):['Another study, conducted by David Cheng'],
    ('cam15-test4',1):['For centuries the huarango tree'],
    ('cam15-test4',3):['Some readers may be disappointed'],
    ('cam18-test3',3):['The practice of ‘streaming’','Despite all this,'],
}

def review_books(books=(15,18,19)):
    reports=[]
    for book,test in [(book,test) for book in books for test in range(1,5)]:
        id=f'cam{book}-test{test}';path=LIB/'tests'/f'{id}.json'
        data=json.loads(path.read_text(encoding='utf-8'));applied=[]
        changes={**COMMON,**CORRECTIONS.get(id,{})}
        for passage in data['passages']:
            paragraphs=[];footnotes=[]
            for p in passage['paragraphs']:
                text=p['text']
                for old,new in changes.items():
                    if old in new and new in text:continue
                    if old in text:text=text.replace(old,new);applied.append([old,new])
                if book==18 and test==2 and passage['number']==2:text=re.sub(r'\bAl\b','AI',text)
                if text.startswith('if extinct species'):text='If'+text[2:]
                if text.startswith('“Mayan:'):
                    footnotes.append({'text':'*'+text[1:]});continue
                footnote='‘Folklorists: those who study traditional stories'
                if text.startswith(footnote):
                    text=text[len(footnote):].strip()
                    footnotes.append({'text':'* Folklorists: those who study traditional stories'})
                    if text and paragraphs and not text[0].isupper():
                        paragraphs[-1]['text']+=' '+text;continue
                pieces=[text]
                for trigger in SPLITS.get((id,passage['number']),[]):
                    pieces=[part for piece in pieces for part in re.split(r'(?='+re.escape(trigger)+')',piece) if part]
                for i,piece in enumerate(pieces):
                    entry={**p,'text':piece.strip()}
                    if i:entry.pop('label',None)
                    paragraphs.append(entry)
            paragraphs.extend(footnotes)
            for i,p in enumerate(paragraphs,1):p['id']=f'p{passage["number"]}-para{i}'
            passage['paragraphs']=paragraphs
            for group in passage['groups']:
                group['instructions'],group['body']=prep.split_directions(group['instructions']+'\n'+group['body'])
                for q in group['questions']:
                    if group['type'] in ['tfng','ynng']:
                        q['text']=re.sub(r'\s+\d{1,3}\s+[>—=|].*$','',q['text']).strip()
                        q['text']=q['text'].replace('/Kung','!Kung')
                if id=='cam18-test2' and passage['number']==1 and group['type']=='tfng':
                    texts=[
                        'During the third phase of construction, sandstone slabs were placed in both the outer areas and the middle of the Stonehenge site.',
                        'There is scientific proof that the bluestones stood in the same spot until approximately 1600 BCE.',
                        'John Aubrey’s claim about Stonehenge was supported by 20th-century findings.',
                        'Objects discovered at Stonehenge seem to indicate that it was constructed by a number of different groups of people.',
                        'Criticism of Gerald Hawkins’ theory about Stonehenge has come mainly from other astronomers.',
                    ]
                    group['questions']=[{'number':9+i,'text':t} for i,t in enumerate(texts)]
                    group['body']='\n\n'.join(f'{9+i}. {t}' for i,t in enumerate(texts))
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        (LIB/'preparation'/'overrides').mkdir(exist_ok=True)
        (LIB/'preparation'/'overrides'/path.name).write_text(path.read_text(encoding='utf-8'),encoding='utf-8')
        reports.append({'test':id,'corrections':applied,'readingSourcePages':[p['sourcePages'] for p in data['passages']]})
    (LIB/'preparation'/'remaining-editorial-review.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':review_books()
