"""Reproducibly extract the user's Cambridge PDFs; never changes source PDFs.

Extraction uses embedded text when available and local Tesseract otherwise.
Raw page text and word coordinates remain available for an auditable review.
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
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library"
PREP = LIB / "preparation"
TESS = PREP / "tessdata"
BOOKS = [13, 14, 15, 17, 18, 19, 20]

def sources():
    out = {}
    for book in BOOKS:
        files = list((ROOT / "Tài liệu Cambridge" / f"CAMBRIDGE-{book}" / "BAN_GOC").glob("*.pdf"))
        if book == 20:
            files.sort(key=lambda p: "Reading" not in p.name)
        if files:
            out[book] = files[0]
    return out

def ensure_tessdata():
    TESS.mkdir(parents=True, exist_ok=True)
    target = TESS / "eng.traineddata"
    if not target.exists():
        urllib.request.urlretrieve("https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata", target)

def extract_page(job):
    import pymupdf
    book, filename, page_no, dpi = job
    folder = PREP / f"cam{book}"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"p{page_no:03}.json"
    if target.exists():
        cached=json.loads(target.read_text(encoding='utf-8'))
        if 'words' in cached and not (cached['method']=='embedded' and 'Tham gia group' in cached['text']) and not (book==15 and cached['method']=='tesseract-eng'):
            return book, page_no, "cached"
    with pymupdf.open(filename) as doc:
        page = doc[page_no - 1]
        embedded = page.get_text()
        use_ocr = len(re.sub(r"\s", "", embedded)) < 100 or 'Tham gia group' in embedded
        # Tesseract's Windows path API cannot open a Unicode absolute path.
        # A relative ASCII path preserves support for the Vietnamese workspace.
        binary=book==15 and use_ocr
        if binary:
            import io
            from PIL import Image,ImageOps
            pix=page.get_pixmap(dpi=dpi,alpha=False)
            im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples).convert('L')
            im=ImageOps.autocontrast(im).point(lambda p:0 if p<195 else 255).convert('RGB')
            buf=io.BytesIO();im.save(buf,format='PNG')
            pix=pymupdf.Pixmap(buf.getvalue())
            ocr=pymupdf.open(stream=pix.pdfocr_tobytes(tessdata=os.path.relpath(TESS,Path.cwd()),language='eng'))
            text=ocr[0].get_text();blocks=ocr[0].get_text('blocks');words=ocr[0].get_text('words')
            scale=page.rect.width/ocr[0].rect.width
            blocks=[tuple(v*scale for v in b[:4])+b[4:] for b in blocks]
            words=[tuple(v*scale for v in w[:4])+w[4:] for w in words]
        else:
            tp = page.get_textpage_ocr(language="eng", dpi=dpi, full=True, tessdata=os.path.relpath(TESS, Path.cwd())) if use_ocr else page.get_textpage()
            text = page.get_text("text", textpage=tp, sort=False)
            blocks = page.get_text("blocks", textpage=tp, sort=False)
            words = page.get_text('words',textpage=tp,sort=False)
            if page.rotation:
                blocks=[tuple(pymupdf.Rect(b[:4])*page.rotation_matrix)+b[4:] for b in blocks]
                words=[tuple(pymupdf.Rect(w[:4])*page.rotation_matrix)+w[4:] for w in words]
        data = {"book":book, "file":str(Path(filename).relative_to(ROOT)), "page":page_no,
                "method":"tesseract-eng-binary" if binary else "tesseract-eng" if use_ocr else "embedded", "dpi":dpi,
                "width":page.rect.width, "height":page.rect.height, "rotation":page.rotation,"text":text,"words":[list(w[:5]) for w in words],
                "blocks":[{"box":list(b[:4]), "text":b[4]} for b in blocks if b[6] == 0]}
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return book, page_no, data["method"]

def extract(args):
    import pymupdf
    ensure_tessdata()
    jobs=[]
    for book,path in sources().items():
        if args.book and book not in args.book:
            continue
        with pymupdf.open(path) as doc:
            last = min(len(doc), args.last or 104) if book != 20 else len(doc)
            for page in range(args.first or 1, last+1):
                if args.reading_only:
                    reading={ref['page'] for f in (LIB/'tests').glob(f'cam{book}-test*.json') for passage in json.loads(f.read_text(encoding='utf-8'))['passages'] for ref in passage['sourcePages']}
                    if page not in reading:continue
                jobs.append((book,str(path),page,args.dpi))
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, result in enumerate(pool.map(extract_page, jobs), 1):
            if i % 10 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} {result}", flush=True)
    overview=[]
    for book in BOOKS:
        for p in sorted((PREP/f"cam{book}").glob("p*.json")):
            d=json.loads(p.read_text(encoding="utf-8"))
            text=d["text"]
            markers=[x.group(0) for x in re.finditer(r"READING\s+PASSAGE\s+[123]|Questions?\s+\d+(?:\s*[-–—]\s*\d+|\s+and\s+\d+)?|WRITING\s+TASK",text,re.I)]
            overview.append(f"{book} p{d['page']:03}: {' | '.join(markers)} :: {text[:90].replace(chr(10),' ')}")
    (PREP/"page-overview.txt").write_text("\n".join(overview),encoding="utf-8")

HEAD = re.compile(r"(?im)^[ \t]*(?:questions?|[a-z]{0,3}estions?|[a-z]{0,3}uestions?|jons)\s+(\d{1,2})(?:\s*(?:[-–—~]|and|&)\s*(\d{1,2}))?[^\n]*")

def load_page(book, page):
    return json.loads((PREP/f"cam{book}"/f"p{page:03}.json").read_text(encoding="utf-8"))

def clean(text):
    lines=text.replace("\r", "").splitlines()
    lines=[re.sub(r"(?:FB\.com|F8\.com|Bcom/|Beom/).*","",line,flags=re.I) for line in lines]
    lines=[line for line in lines if not re.search(r"LouisQuang|thread: dongan|Làm đề|Website tự|ielts-fighter\.com|Tham gia group|facebook.com/groups",line,re.I)]
    while lines and (not lines[0].strip() or re.fullmatch(r"\s*(?:Test\s+\d|Reading|[|;_—=~.\s-]+)\s*",lines[0],re.I)):
        lines.pop(0)
    while lines and (not lines[-1].strip() or re.fullmatch(r"\s*\d{1,3}\s*",lines[-1])):
        lines.pop()
    return "\n".join(lines).strip()

def remove_intro(text):
    text=clean(text)
    text=re.sub(r"(?s)^.*?READING\s+PASSAGE\s*[123]\s*", "", text, count=1)
    text=re.sub(r"(?is)^.*?You should spend.*?Passage\s*[1-9]\d?\s*(?:below|on pages?[^.]*|on the following pages)\.", "",text,count=1)
    text=re.sub(r"(?s)^.*?You should spend.*?Passage\s*[123]\.", "",text,count=1)
    return clean(text)

def infer_type(body):
    text=re.sub(r"\s+"," ",body).lower()
    if re.search(r"choose\s+(two|three)\s+letters",text): return "multi"
    if "true" in text and "false" in text and ("not given" in text or "following statements" in text): return "tfng"
    if re.search(r"\byes\b",text) and re.search(r"\bno\b",text) and "not given" in text: return "ynng"
    if "choose the correct letter" in text: return "choice"
    if any(x in text for x in ["correct heading","correct ending","match each", "which paragraph", "which section", "list of", "choose five answers", "choose four answers", "choose six answers"]): return "matching"
    if re.search(r"answer the questions",text): return "short"
    return "completion"

def option_list(text):
    matches=list(re.finditer(r"(?m)^[ \t]*([A-J]|i{1,3}|iv|vi{0,3}|ix|x)(?![A-Za-z])[ \t._-]*(?:\n[ \t]*)?([^\n]*)",text))
    opts=[]
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        value=m.group(1); label=text[m.start(2):end]
        label=re.split(r"\bQuestions?\s+\d|\n\s*\d{1,2}\b",label)[0]
        label=re.sub(r"\s+"," ",label).strip()
        if label and value not in [o['value'] for o in opts]: opts.append({"value":value,"label":label})
    return opts

def split_directions(body):
    body=HEAD.sub('',body,count=1).strip()
    lines=body.splitlines(); directions=[]; stop=0; continuation=False
    command=re.compile(r"^(?:Complete\b|Choose\b|Write\b|Look\b|Match\b|Answer\b|Do the following\b|In boxes\b|NB\b|Reading Passage \d+ has\b|Which (?:paragraph|section)\b)",re.I)
    definition=re.compile(r"^(?:TRUE|FALSE|NOT GIVEN|YES|NO|if the statement|if there is|if it is)\b",re.I)
    for i,line in enumerate(lines):
        s=line.strip()
        if not s: stop=i+1;continue
        if re.match(r'^\d{1,2}(?:\b|[.)])',s):break
        if command.search(s) or definition.search(s) or continuation:
            directions.append(s);stop=i+1
            continuation=not bool(re.search(r"[.?:]$",s)) and not s.endswith('write')
            if re.match(r'^(TRUE|FALSE|NOT GIVEN|YES|NO)$',s):continuation=False
            continue
        break
    return '\n'.join(directions),'\n'.join(lines[stop:]).strip()

def paragraph_breaks(data,text):
    # OCR sometimes joins all paragraphs into a single text block. Recover
    # paragraph spacing from source coordinates without altering the words.
    if data['book']==15 or (data['book'],data['page']) in [(17,17),(17,18),(18,72),(18,73),(19,47),(19,48)]:return text
    previous=None
    for block in data['blocks']:
        part=clean(block['text'])
        if not part or part not in text:continue
        if previous and block['box'][1]-previous['box'][3]>6:
            text=text.replace(part,'\n\n'+part,1)
        previous=block
    return text

OPTION_REPAIRS={
    (15,2,32):{'G':'enjoyment'},
    (15,3,27):{'B':'are the reason for their survival.'},
    (15,3,32):{'G':'horror','I':'plot'},
    (17,1,27):{'I':'popular solution'},
    (18,1,19):{'A':'a TSI Cut','B':'a Salvage Cut','C':'a Shelterwood Cut'},
    (18,3,31):{'A':'wrong classes','B':'lower expectations','C':'average learners','D':'bottom sets','E':'brightest pupils','F':'disadvantaged backgrounds','G':'weaker students','H':'higher achievements','I':'positive impressions'},
    (19,1,31):{'D':'experimental subjects','E':'short period','I':'dubious reason'},
    (19,2,27):{'I':'innovative','K':'intent'},
    (19,3,31):{'B':'as systems do not need to conform to standard practices.'},
}

def repair_options(book,test,lo,body,options):
    romans=['i','ii','iii','iv','v','vi','vii','viii','ix','x']
    if sum(o['value'] in romans for o in options)>=3:
        return [o for o in options if o['value'] in romans]
    match=re.search(r'\b([A-Z])\s*[-–—~]+\s*([A-Z])\b',body)
    if match:
        allowed=[chr(n) for n in range(ord(match[1]),ord(match[2])+1)]
        values={o['value']:o['label'] for o in options if o['value'] in allowed}
        values.update(OPTION_REPAIRS.get((book,test,lo),{}))
        return [{'value':v,'label':values[v]} for v in allowed if v in values]
    repairs=OPTION_REPAIRS.get((book,test,lo),{})
    if repairs:
        values={o['value']:o['label'] for o in options if re.fullmatch('[A-Z]',o['value'])}
        values.update(repairs)
        return [{'value':v,'label':values[v]} for v in sorted(values)]
    return options

def word_lines(words):
    rows=[]
    for word in sorted(words,key=lambda w:(w[1],w[0])):
        if rows and abs(word[1]-rows[-1][0][1])<3:
            rows[-1].append(word)
        else:rows.append([word])
    result=[];previous=None
    for row in rows:
        row.sort(key=lambda w:w[0]);y=min(w[1] for w in row)
        height=max(w[3]-w[1] for w in row)
        if previous is not None and y-previous>height*1.8:result.append('')
        # Paragraph letters are set in a separate left margin in the original.
        if len(row)>1 and re.fullmatch('[A-H]',row[0][4]) and row[1][0]-row[0][2]>8:
            result.append(row[0][4]);row=row[1:]
        result.append(' '.join(w[4] for w in row));previous=y
    return '\n'.join(result)

def normalize_reading_text(text):
    # Mechanical OCR repairs only. Vocabulary and meaning remain source-led.
    text=re.sub(r'\bof(?=[A-Z0-9])','of ',text)
    text=re.sub(r'\b(off|of|if|and|on|how|through|by|as|myself|itself)(?=(?:the|these|those|this|that|people|water|metres|trees|pride|psychology|justice|money|his|their|humour|traffic|insects|modern|competition|most|spices|professions|remote|what|tough|islands|nutmeg|a|you|they|to|by)\b)',r'\1 ',text)
    text=re.sub(r'\s*[|_]\s*',' ',text)
    text=text.replace('o f today', 'of today').replace('si lbadores','silbadores')
    return re.sub(r'\s+',' ',text).strip()

def layout_text(data):
    words=data.get('words',[])
    if not words:return data['text']
    if data['book']==15 and data['page'] in [18,19,22,23,26,27,39,40,42,43,46,47,60,61,65,66,68,69,82,83,86,87,90,91]:
        # Pale scan edges are read as spurious i / | / punctuation. They sit
        # outside the printed text column, so reject them geometrically.
        anchors=[w for w in words if 130<w[1]<data['height']-100 and len(re.sub(r'[^a-zA-Z]','',w[4]))>=4]
        lo=min(w[0] for w in anchors)-4 if anchors else 35
        hi=max(w[2] for w in anchors)+4 if anchors else data['width']-35
        words=[w for w in words if w[1]<data['height']-45 and (len(w[4])>1 or re.fullmatch('[A-H0-9]',w[4]) or lo<=w[0]<hi)]
        words=[w for w in words if not (w[1]>data['height']*.88 and re.fullmatch(r'\d{1,3}',w[4]))]
        return word_lines(words)
    if data['book']==15:return data['text']
    # Cambridge17's source scan has a QR watermark above the page header.
    low=75 if data['book']==17 else 35
    words=[w for w in words if low<=w[1]<data['height']-35 and not (w[1]>data['height']*.8 and re.fullmatch(r'\d{1,3}',w[4]))]
    body=[w for w in words if 155<w[1]<data['height']-60]
    if len(body)<200:
        if data['book']==17:
            text=data['text']
            for block in data['blocks']:
                if block['box'][3]<75:text=text.replace(block['text'],'')
            return text
        return data['text']
    left=min(w[0] for w in body);right=max(w[2] for w in body);width=right-left
    candidates=[left+width*f/100 for f in range(43,58)]
    split=min(candidates,key=lambda x:sum(w[0]<x+2 and w[2]>x-2 for w in body))
    crossing=sum(w[0]<split+2 and w[2]>split-2 for w in body)
    if crossing>10:
        if data['book']==17:
            text=data['text']
            for block in data['blocks']:
                if block['box'][3]<75:text=text.replace(block['text'],'')
            return text
        return data['text']
    rows=[]
    for w in sorted(words,key=lambda x:(x[1],x[0])):
        if rows and abs(w[1]-rows[-1][0][1])<3:rows[-1].append(w)
        else:rows.append([w])
    known_starts={(17,17):232,(17,18):78,(18,72):157,(18,73):58,(19,47):190,(19,48):64}
    start=known_starts.get((data['book'],data['page']))
    for row in rows:
        if start is not None:break
        if min(w[1] for w in row)<max(low,70):continue
        l=[w for w in row if w[2]<split-2];r=[w for w in row if w[0]>split+2]
        cross=[w for w in row if w[0]<split+2 and w[2]>split-2]
        if len(l)>=4 and len(r)>=4 and not cross:
            start=min(w[1] for w in row)-2;break
    if start is None:return data['text']
    footnote_y=min([w[1] for w in words if w[4]=='*' and w[1]>data['height']*.8]+[data['height']])
    footnotes=[w for w in words if w[1]>=footnote_y]
    words=[w for w in words if w[1]<footnote_y]
    header=[w for w in words if w[1]<start]
    l=[w for w in words if w[1]>=start and (w[0]+w[2])/2<split]
    r=[w for w in words if w[1]>=start and (w[0]+w[2])/2>=split]
    return '\n\n'.join([word_lines(header),word_lines(l),word_lines(r),word_lines(footnotes)])

def question_entries(body, lo, hi, kind):
    result=[]
    for number in range(lo,hi+1):
        # The complete question block is authoritative; a short field label is
        # supplied when its numbered statement is reliably extractable.
        pat=re.compile(rf"(?m)^\s*{number}\s*[.)]?\s+(?P<t>[^\n].*)")
        m=pat.search(body)
        text=""
        opts=None
        if m:
            tail=body[m.start():]
            nextq=re.search(rf"(?m)^\s*(?:{'|'.join(str(n) for n in range(number+1,hi+1)) or '999'})\s*[.)]?\s+",tail[1:])
            chunk=tail[:nextq.start()+1] if nextq else tail
            text=re.sub(r"\s+"," ",chunk[len(m.group(0))-len(m.group('t')):]).strip()
            if kind=="choice":
                opts=[o for o in option_list(chunk) if o['value'] in list('ABCD')]
                text=re.split(r"\s[A-D]\s*[.]?\s+",text,maxsplit=1)[0]
            else:
                text=re.split(r"List of|Questions?\s+\d",text)[0].strip()
        entry={"number":number,"text":text}
        if kind=='choice': entry['options']=opts if opts and len(opts)==4 else [{"value":c,"label":next((o['label'] for o in opts or [] if o['value']==c),c)} for c in 'ABCD']
        result.append(entry)
    return result

def page_y(data, marker, end=False):
    number_match=re.search(r"\d+",marker)
    number=number_match.group() if number_match else ""
    for b in data["blocks"]:
        if re.search(r"(?:[Qq]uestions?|[a-zA-Z]{1,4}estions?)\s+"+re.escape(number)+r"\b",b["text"]):
            return b['box'][3] if end else b['box'][1]
    return 48

def source_image(book, page_no, slug, top=None, bottom=None):
    import pymupdf
    from PIL import Image
    bounds=hashlib.sha256(json.dumps([3,book,page_no,top,bottom]).encode()).hexdigest()[:8]
    target=LIB/"assets"/f"{slug}-{bounds}.webp"
    if not target.exists():
        with pymupdf.open(sources()[book]) as doc:
            page=doc[page_no-1]
            data=load_page(book,page_no)
            footer=page.rect.height
            # Exclude source watermark/footer but never crop a question line.
            for block in data["blocks"]:
                if re.search(r"thread: dongan",block['text']): footer=min(footer,block['box'][1]-3)
            clip=page.rect if '-reading-' in slug else pymupdf.Rect(0,max(0,(top or 0)-5),page.rect.width,min(bottom or footer,footer))
            if clip.height < 10: clip=page.rect
            pix=page.get_pixmap(dpi=155,clip=clip,alpha=False)
            im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
            target.parent.mkdir(parents=True,exist_ok=True)
            im.save(target,"WEBP",quality=88)
    return {"url":"/library-assets/"+target.name,"page":page_no}

def section_content(book, test, passage_no, pages):
    pieces=[]; groups=[]; source_pages=[]; images=[]; passage_chunks=[]
    in_questions=False; heading_precedes_passage=False
    for page_no in pages:
        data=load_page(book,page_no)
        page_text=layout_text(data)
        text=remove_intro(page_text) if "READING PASSAGE" in re.sub(r"\s+"," ",page_text) else clean(page_text)
        if book==15 and page_no==48: text=re.sub(r'(?m)^Bs\s*$', 'B',text)
        if book==15 and page_no==93: text=re.sub(r'(?m)^DA\s*\nfast-food', 'D\nA fast-food',text)
        if book==18 and page_no==92: text=re.sub(r'(?m)^45\s*\nThe second', '15\nThe second',text)
        if book==18 and page_no==89: text=text.replace('Bmore economical','B more economical')
        if book==19 and page_no==22: text=text.replace('EA favourable','E A favourable')
        if book==20 and page_no==54: text="Questions 14-19\n\n"+text
        if book==20 and page_no==57: text=text.replace("Complete the sentences below.","Questions 24-26\n\nComplete the sentences below.")
        if book==20 and page_no==19:
            text=text.replace("Being aware of the \ninformation", "Being aware of the close relationship between people's emotional state and how they process \ninformation")
        matches=list(HEAD.finditer(text))
        source_pages.append({"file":data['file'],"page":page_no})
        if not matches:
            if in_questions and not heading_precedes_passage:
                if groups:
                    groups[-1]['segments'].append((page_no,text,None,None))
            else:
                passage_chunks.append(paragraph_breaks(data,text))
                images.append(source_image(book,page_no,f"cam{book}-t{test}-p{passage_no}-reading-{page_no:03}"))
                heading_precedes_passage=False; in_questions=False
            continue
        first=matches[0]
        prefix=clean(text[:first.start()])
        if len(re.sub(r'\W','',prefix))<5:prefix=''
        if prefix:
            if in_questions and not heading_precedes_passage and groups:
                groups[-1]['segments'].append((page_no,prefix,None,page_y(data,first.group())))
            else:
                passage_chunks.append(paragraph_breaks(data,prefix))
                images.append(source_image(book,page_no,f"cam{book}-t{test}-p{passage_no}-reading-{page_no:03}",bottom=page_y(data,first.group())-3))
        for i,match in enumerate(matches):
            stop=matches[i+1].start() if i+1<len(matches) else len(text)
            body=text[match.start():stop].strip()
            # Ranges embedded in instructions can be repeated on their own
            # line by OCR; a true group starts with its instructions.
            lo=int(match[1]);hi=int(match[2] or match[1])
            if hi<lo or lo<1 or hi>40: continue
            if groups and lo==groups[-1]['lo'] and hi==groups[-1]['hi']:
                groups[-1]['segments'].append((page_no,body,page_y(data,match.group()),None))
                continue
            groups.append({"lo":lo,"hi":hi,"segments":[(page_no,body,page_y(data,match.group()),page_y(data,matches[i+1].group())-3 if i+1<len(matches) else None)]})
        in_questions=True
        if not passage_chunks and any("heading" in s[1].lower() for g in groups for s in g['segments']):
            heading_precedes_passage=True
    clean_groups=[]
    prior=(0,13,26)[passage_no-1]
    for gi,g in enumerate(groups):
        lo=max(g['lo'],prior+1); hi=g['hi']
        if hi<lo: continue
        body="\n\n".join(s[1] for s in g['segments'])
        kind=infer_type(body)
        group_id=f"cam{book}-t{test}-p{passage_no}-g{gi+1}"
        instructions,question_body=split_directions(body)
        sg={"id":group_id,"type":kind,"heading":f"Questions {lo}–{hi}","instructions":instructions,"body":question_body,"questions":question_entries(body,lo,hi,kind),"sourceImages":[]}
        for si,(page_no,_,top,bottom) in enumerate(g['segments']):
            sg['sourceImages'].append(source_image(book,page_no,f"{group_id}-s{si+1}",top,bottom))
        if kind in ('completion','short'):
            match=re.search(r"(ONE|TWO|THREE|FOUR)\s+WORDS?",body,re.I)
            if match: sg['wordLimit']={"ONE":1,"TWO":2,"THREE":3,"FOUR":4}[match.group(1).upper()]
            sg['allowNumber']=bool(re.search(r"A NUMBER|NUMBERS?",body,re.I))
        if kind=='multi': sg['choose']=hi-lo+1
        if kind=='matching':
            opts=option_list(body)
            if not opts:
                match=re.search(r"\b([A-I])\s*[-–—]\s*([A-J])\b",body)
                if match: opts=[{"value":chr(n),"label":chr(n)} for n in range(ord(match[1]),ord(match[2])+1)]
            sg['options']=repair_options(book,test,lo,body,opts)
        if kind=='multi': sg['options']=repair_options(book,test,lo,body,[o for o in option_list(body) if o['value'] in list('ABCDE')])
        if book!=20 and (kind in ('completion','short') or (kind=='matching' and 'summary' in body.lower())):
            sg['renderMode']='source'
        clean_groups.append(sg);prior=hi
    joined='\n\n'.join(passage_chunks)
    lines=joined.splitlines()
    while lines and len(re.sub(r'\W','',lines[0]))<5: lines.pop(0)
    title=lines.pop(0).strip() if lines else f"Reading Passage {passage_no}"
    title_continuations={(14,1,2):'the world',(15,4,2):'the Canary Islands',(17,3,3):'Skyscrapers',(18,4,3):'of continental drift',(19,2,3):'gifted child',(19,3,1):'prehistoric island settlers'}
    suffix=title_continuations.get((book,test,passage_no))
    while suffix and lines and not lines[0].strip():lines.pop(0)
    if suffix and lines and lines[0].strip()==suffix:
        title+=' '+lines.pop(0).strip()
    if (book,test,passage_no)==(14,4,3):
        lines.insert(0,title);title='Marine debris'
    # Embedded text retains paragraph breaks. OCR blocks are available in raw
    # extraction for manual editorial correction; avoid changing word order.
    remainder='\n'.join(lines).strip()
    remainder=re.sub(r'(?m)^([A-H])[ \t]*[._—-]+[ \t]*',r'\n\n\1\n',remainder)
    remainder=re.sub(r'(?m)^([A-H])(?=A\s)',r'\n\n\1\n',remainder)
    chunks=re.split(r"\n\s*\n|\n(?=[A-H]\s*\n)",remainder)
    paragraphs=[];pending_label=None;pending_prefix=''
    for i,chunk in enumerate(chunks):
        chunk=chunk.strip()
        if not chunk: continue
        if re.fullmatch(r'[A-H]',chunk):
            if pending_label and chunk=='A':pending_prefix='A ';continue
            pending_label=chunk;continue
        if len(re.sub(r'\W','',chunk))<3:continue
        label=None
        match=re.match(r"^([A-H])\s*[.]?\s*\n",chunk)
        if match: label=match[1];chunk=chunk[match.end():]
        if not label and pending_label:label=pending_label;pending_label=None
        if pending_prefix:chunk=pending_prefix+chunk;pending_prefix=''
        normalized=normalize_reading_text(chunk)
        if paragraphs and not label and normalized and normalized[0].islower() and not re.search(r'[.!?][\'"’”)]?$',paragraphs[-1]['text']):
            paragraphs[-1]['text']+=' '+normalized
            continue
        p={"id":f"p{passage_no}-para{i+1}","text":normalized}
        if label:p['label']=label
        paragraphs.append(p)
    return {"id":f"cam{book}-test{test}-p{passage_no}","number":passage_no,"title":title,"paragraphs":paragraphs,"groups":clean_groups,"sourcePages":source_pages,"sourceImages":images}

def discover_sections(book):
    starts=[];write=[]
    for path in sorted((PREP/f"cam{book}").glob('p*.json')):
        d=json.loads(path.read_text(encoding='utf-8'))
        match=re.search(r"(?m)^\s*READING\s+PASSAGE\s*([123])(?:\W|_)",d['text'])
        if match: starts.append((d['page'],int(match[1])))
        if re.search(r"(?m)^\s*WRITING\s+TASK",d['text']): write.append(d['page'])
    sections=[]
    for i,(page,no) in enumerate(starts):
        next_start=starts[i+1][0] if i+1<len(starts) else 105
        end=min([x for x in write if x>page]+[next_start])-1
        sections.append((no,list(range(page,end+1))))
    return sections

def assemble(args):
    (LIB/'tests').mkdir(parents=True,exist_ok=True)
    report=[]
    for book in args.book or BOOKS:
        if book==20:
            # Canonical text-bearing PDF: explicit passage/question ranges.
            ranges=[[(7,11),(12,16),(17,22)],[(29,32),(33,37),(38,43)],[(50,53),(54,57),(58,62)],[(68,72),(73,76),(77,80)]]
            sections=[(n,list(range(a,b+1))) for test in ranges for n,(a,b) in enumerate(test,1)]
        elif book==15:
            ranges=[[(18,21),(22,25),(26,29)],[(39,41),(42,45),(46,50)],[(60,63),(64,67),(68,72)],[(82,85),(86,89),(90,94)]]
            sections=[(n,list(range(a,b+1))) for test in ranges for n,(a,b) in enumerate(test,1)]
        else: sections=discover_sections(book)
        if len(sections)!=12:
            raise ValueError(f'Cambridge {book}: expected12 passages, found {sections}')
        for test in range(1,5):
            if args.test and test not in args.test:continue
            passages=[section_content(book,test,no,pages) for no,pages in sections[(test-1)*3:test*3]]
            item={"id":f"cam{book}-test{test}","book":book,"test":test,"title":f"Cambridge {book} · Test {test}","version":"2026-10-21.1","verification":{"status":"needs_review","note":"Extracted from the local source PDFs. Exact source images accompany question blocks; editorial review is recorded in preparation reports."},"passages":passages}
            override=PREP/'overrides'/f"{item['id']}.json"
            override_bytes=override.read_bytes() if override.exists() else None
            if override_bytes is not None: item=json.loads(override_bytes.decode('utf-8'))
            passages=item['passages']
            output=LIB/'tests'/f"{item['id']}.json"
            if override_bytes is not None:output.write_bytes(override_bytes)
            else:output.write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
            numbers=[q['number'] for p in passages for g in p['groups'] for q in g['questions']]
            report.append({"id":item['id'],"titles":[p['title'] for p in passages],"questionNumbers":numbers,"missing":sorted(set(range(1,41))-set(numbers)),"duplicates":sorted({n for n in numbers if numbers.count(n)>1}),"groups":[[g['heading'],g['type']] for p in passages for g in p['groups']]})
            print(item['id'],len(numbers),'questions',flush=True)
    (PREP/'content-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

def refresh_images(args):
    report=[]
    for filename in sorted((LIB/'tests').glob('cam*-test*.json')):
        item=json.loads(filename.read_text(encoding='utf-8'))
        book=item['book'];test=item['test']
        if args.book and book not in args.book:continue
        for passage in item['passages']:
            number=passage['number'];new=[]
            for ref in passage.get('sourceImages',[]):
                if 'alternate' in ref['url']:
                    new.append(ref);continue
                new.append({**ref,**source_image(book,ref['page'],f'cam{book}-t{test}-p{number}-reading-{ref["page"]:03}')})
            passage['sourceImages']=new
            for group in passage['groups']:
                lo=min(q['number'] for q in group['questions']);hi=max(q['number'] for q in group['questions']);new=[]
                for i,ref in enumerate(group.get('sourceImages',[]),1):
                    data=load_page(book,ref['page']);matches=list(HEAD.finditer(clean(data['text'])))
                    own=[m for m in matches if int(m[1])==lo or (int(m[2] or m[1])==hi and int(m[1])<=lo)]
                    top=page_y(data,own[0].group()) if own else None
                    following=[m for m in matches if int(m[1])>hi]
                    bottom=page_y(data,following[0].group())-3 if following else None
                    new.append({**ref,**source_image(book,ref['page'],f'{group["id"]}-s{i}',top,bottom)})
                group['sourceImages']=new
        filename.write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
        override=PREP/'overrides'/filename.name
        if override.exists():override.write_text(filename.read_text(encoding='utf-8'),encoding='utf-8')
        report.append(item['id']);print('Refreshed',item['id'],flush=True)
    (PREP/'image-refresh.json').write_text(json.dumps({'cropVersion':3,'reading':'Full original page bounds; no text-edge/footer clipping.','questions':'Full page width, group heading through the next question group or original page end.','tests':report},ensure_ascii=False,indent=2),encoding='utf-8')

def provenance(args):
    import pymupdf
    records=[]
    files=list(sources().values())
    files.extend(p for p in (ROOT/'Tài liệu Cambridge'/'CAMBRIDGE-20'/'BAN_GOC').glob('*.pdf') if p not in files)
    for filename in files:
        with pymupdf.open(filename) as doc:pages=len(doc)
        records.append({'file':str(filename.relative_to(ROOT)),'bytes':filename.stat().st_size,'pages':pages,'sha256':hashlib.sha256(filename.read_bytes()).hexdigest()})
    model=TESS/'eng.traineddata'
    output={'sources':records,'ocr':{'engine':'PyMuPDF / Tesseract','pymupdfVersion':pymupdf.__version__,'language':'eng','dpi':200,'model':'tessdata_fast','modelUrl':'https://github.com/tesseract-ocr/tessdata_fast/blob/main/eng.traineddata','modelSha256':hashlib.sha256(model.read_bytes()).hexdigest()},'sourcePolicy':'Original PDFs are only read. Editorial corrections and complete source references are stored separately.'}
    (PREP/'sources.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Recorded',len(records),'source PDF hashes')

def asset_report(args):
    assets=(LIB/'assets').resolve()
    if assets.parent!=LIB.resolve():raise ValueError('Unsafe asset root')
    references={Path(ref['url']).name for file in (LIB/'tests').glob('*.json') for passage in json.loads(file.read_text(encoding='utf-8'))['passages'] for entity in [passage]+passage['groups'] for ref in entity.get('sourceImages',[])}
    unused=[p for p in assets.iterdir() if p.is_file() and re.fullmatch(r'cam\d+-.+\.webp',p.name) and p.name not in references]
    total=sum(p.stat().st_size for p in unused)
    print(json.dumps({'imagesNotReferencedByCurrentLibrary':len(unused),'bytes':total,'removed':False,'retainedForHistoricalAttempts':True}))

def main():
    os.chdir(ROOT)
    parser=argparse.ArgumentParser(__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("extract");p.add_argument("--book",type=int,nargs="+");p.add_argument("--first",type=int);p.add_argument("--last",type=int);p.add_argument("--dpi",type=int,default=200);p.add_argument("--workers",type=int,default=4);p.add_argument('--reading-only',action='store_true')
    p=sub.add_parser("assemble");p.add_argument("--book",type=int,nargs="+");p.add_argument('--test',type=int,nargs='+')
    p=sub.add_parser('refresh-images');p.add_argument('--book',type=int,nargs='+')
    sub.add_parser('provenance')
    sub.add_parser('asset-report')
    args=parser.parse_args()
    if args.command == "extract": extract(args)
    elif args.command == "assemble": assemble(args)
    elif args.command == 'refresh-images':refresh_images(args)
    elif args.command == 'provenance':provenance(args)
    elif args.command == 'asset-report':asset_report(args)

if __name__ == "__main__":
    if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    main()
