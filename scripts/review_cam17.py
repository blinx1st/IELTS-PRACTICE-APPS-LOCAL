"""Reviewed corrections against the supplied Cambridge 17 scan.

The overrides produced here preserve manual editorial fixes when re-importing.
"""
import json
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "library/tests"
OVERRIDES = ROOT / "library/preparation/overrides"
OVERRIDES.mkdir(parents=True, exist_ok=True)


def clean_string(s):
    replacements = {"formeda": "formed a", " asa ": " as a ", "ofthe": "of the", "ofthree": "of three", "ofArles": "of Arles", "ofjust": "of just", "ofanew": "of a new", "huntfor": "hunt for", "througha": "through a", "anda ": "and a ", "havea": "have a", "newgovernment": "new government", "Hechose": "He chose", "Hechooses": "He chooses", "Adifferent": "A different", "wasa ": "was a ", "amention": "a mention", "Zo Catch": "To Catch", "day-by- day": "day-by-day", "eye- rolling": "eye-rolling"}
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = re.sub(r"\s*[>3/|@ ]*@?\s*p\.\s*1[12]\d\s*[\])|]*\s*$", "", s)
    s = re.sub(r"^[~=_]+\s*", "", s)
    s = re.sub(r"(?<!_)\s+_{1,2}(?!_)\s+", " ", s)
    s = re.sub(r"(?<=[.?!])\s+\d{2,3}\s*[=+|>~]*\s*$", "", s)
    for old, new in {"nose- to-tail": "nose-to-tail", "ofTasmania": "of Tasmania", "ofa ": "of a ", "playeda": "played a", "ofoil": "of oil", "becomea": "become a", "oflegends": "of legends", "ofbuilding": "of building", "ofhow": "of how", "boomof": "boom of", "bedrock*™*": "bedrock**", "_Itgives": "It gives", "Itis ": "It is ", "lts membership": "Its membership", "lt contains": "It contains"}.items():
        s = s.replace(old, new)
    for old, new in {"CE,is": "CE, is", "Journal—": "Journal —", "areference": "a reference", "anumber": "a number", "acomparison": "a comparison", "apersonal": "a personal", "ona ": "on a ", "by a relatively": "by a relatively", "bya ": "by a ", "notionsofinsight": "notions of insight", "ofNatural": "of Natural", "ofdiscoveries": "of discoveries", "Inthe": "In the"}.items():
        s = s.replace(old, new)
    for old, new in {"Muchofthis": "Much of this", "ofbats": "of bats", "education- related": "education-related", "insteadoflistening": "instead of listening", "Riethmiillerin": "Riethmüllerin", "aclaim": "a claim", "areason": "a reason", "UCLAi\\is": "UCLA is", "‘| ": "‘I ", "that | ": "that I ", "to. | ": "to. I ", "‘I’m very optimistic, says": "‘I’m very optimistic,’ says"}.items():
        s = s.replace(old, new)
    return s.strip()


def walk(obj):
    if isinstance(obj, dict):
        return {k: walk(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v) for v in obj]
    return clean_string(obj) if isinstance(obj, str) else obj


def normalize_paragraphs(test):
    for p in test["passages"]:
        notes = []
        paragraphs = []
        for par in p["paragraphs"]:
            if re.match(r"^\*{1,2} ", par["text"]) or par.get("kind") == "footnote":
                par["kind"] = "footnote"
                notes.append(par)
            else:
                paragraphs.append(par)
        notes.sort(key=lambda a: len(a["text"]) - len(a["text"].lstrip("*")))
        p["paragraphs"] = paragraphs + notes
        for i, par in enumerate(p["paragraphs"]):
            par["id"] = f"{p['id']}-para{i+1}"
        for g in p["groups"]:
            lo, hi = g["questions"][0]["number"], g["questions"][-1]["number"]
            if g["type"] in ("tfng", "ynng"):
                info = g["type"] == "tfng"
                g["instructions"] = (f"Do the following statements agree with the {'information given' if info else 'claims of the writer'} in Reading Passage {p['number']}?\nIn boxes {lo}–{hi} on your answer sheet, write:\n"
                    + ("TRUE — if the statement agrees with the information\nFALSE — if the statement contradicts the information\nNOT GIVEN — if there is no information on this" if info else "YES — if the statement agrees with the claims of the writer\nNO — if the statement contradicts the claims of the writer\nNOT GIVEN — if it is impossible to say what the writer thinks about this"))
            if g["type"] == "multi" and g.get("options"):
                body = g["body"]
                match = re.search(r"(?:^|\n)A\s*[_—~-]*\s*(?:\n| )", body)
                if match:
                    g["body"] = body[:match.start()].strip()
            for q in g["questions"]:
                if g["type"] == "completion":
                    q["text"] = ""
                if q.get("options"):
                    q["text"] = re.split(r"\s+A[_—~ -]{1,}\s*", q["text"], maxsplit=1)[0].strip()
            if g["type"] in ("tfng", "ynng", "choice"):
                # Body remains a source transcription; UI displays each cleaned question.
                pass
            if g.get("wordLimit") and "NUMBER" not in g["instructions"].upper():
                g["allowNumber"] = False


def test1(t):
    p1, p2, p3 = t["passages"]
    p1["groups"][0]["body"] = """The London underground railway

The problem
• The 1 __________ of London increased rapidly between 1800 and 1850
• The streets were full of horse-drawn vehicles

The proposed solution
• Charles Pearson, a solicitor, suggested building an underground railway
• Building the railway would make it possible to move people to better housing in the 2 __________
• A number of 3 __________ agreed with Pearson's idea
• The company initially had problems getting the 4 __________ needed for the project
• Negative articles about the project appeared in the 5 __________

The construction
• The chosen route did not require many buildings to be pulled down
• The 'cut and cover' method was used to construct the tunnels
• With the completion of the brick arch, the tunnel was covered with 6 __________"""
    p1["groups"][0].pop("renderMode", None)
    p2["groups"][1]["body"] = """Roman amphitheatres

The Roman stadiums of Europe have proved very versatile. The amphitheatre of Arles, for example, was converted first into a 18 __________, then into a residential area and finally into an arena where spectators could watch 19 __________. Meanwhile, the arena in Verona, one of the oldest Roman amphitheatres, is famous today as a venue where 20 __________ is performed. The site of Lucca's amphitheatre has also been used for many purposes over the centuries, including the storage of 21 __________. It is now a market square with 22 __________ and homes incorporated into the remains of the Roman amphitheatre."""
    p2["groups"][1].pop("renderMode", None)
    p3["paragraphs"][0]["kind"] = "subtitle"
    for par in p3["paragraphs"]:
        par["text"] = par["text"].replace("far _—_-more", "far more").replace("Indeed, _ the", "Indeed, the").replace("hiding —_must", "hiding must").replace("pleasure-loving |= monarch", "pleasure-loving monarch")
    summary = p3["groups"][0]
    summary["body"] = """The story behind the hunt for Charles II

Charles II's father was executed by the Parliamentarian forces in 1649. Charles II then formed a 27 __________ with the Scots, and in order to become King of Scots, he abandoned an important 28 __________ that was held by his father and had contributed to his father's death. The opposing sides then met outside Worcester in 1651. The battle led to a 29 __________ for the Parliamentarians and Charles had to flee for his life. A 30 __________ was offered for Charles's capture, but after six weeks spent in hiding, he eventually managed to reach the 31 __________ of continental Europe."""
    labels = ["military innovation", "large reward", "widespread conspiracy", "relative safety", "new government", "decisive victory", "political debate", "strategic alliance", "popular solution", "religious conviction"]
    summary["options"] = [{"value": chr(65+i), "label": label} for i, label in enumerate(labels)]
    summary.pop("renderMode", None)


def test2(t):
    p1, p2, p3 = t["passages"]
    p1["groups"][0]["body"] = """The Dead Sea Scrolls

Discovery
Qumran, 1946/7
• three Bedouin shepherds in their teens were near an opening on side of cliff
• heard a noise of breaking when one teenager threw a 1 __________
• teenagers went into the 2 __________ and found a number of containers made of 3 __________

The scrolls
• date from between 150 BCE and 70 CE
• thought to have been written by group of people known as the 4 __________
• written mainly in the 5 __________ language
• most are on religious topics, written using ink on parchment or papyrus"""
    p1["groups"][0].pop("renderMode", None)
    for par in p2["paragraphs"]:
        if par.get("label") == "D":
            par["text"] = par["text"].removeprefix("= ")
    p2["groups"][2]["body"] = """24 An undesirable trait such as loss of __________ may be caused by a mutation in a tomato gene.

25 By modifying one gene in a tomato plant, researchers made the tomato three times its original __________.

26 A type of tomato which was not badly affected by __________, and was rich in vitamin C, was produced by a team of researchers in China."""
    p2["groups"][2].pop("renderMode", None)
    p3["paragraphs"][0]["kind"] = "subtitle"
    g = p3["groups"][2]
    g["body"] = """The origins of creative behaviour

The traditional view of scientific discovery is that breakthroughs happen when a single great mind has sudden 37 __________. Although this can occur, it is not often the case. Advances are more likely to be the result of a longer process. In some cases, this process involves 38 __________, such as Nicholson's theory about proto-elements. In others, simple necessity may provoke innovation, as with Westrope's decision to modify the position of his riding stirrups. There is also often an element of 39 __________, for example, the coincidence of ideas that led to the invention of the Post-It note. With both the Law of Natural Selection and the Law of Effect, there may be no clear 40 __________ involved, but merely a process of variation and selection."""
    g["options"] = [{"value": chr(65+i), "label": text} for i, text in enumerate(["invention", "goals", "compromise", "mistakes", "luck", "inspiration", "experiments"])]
    g.pop("renderMode", None)


def test3(t):
    p1, p2, p3 = t["passages"]
    p1["groups"][0]["body"] = """The thylacine

Appearance and behaviour
• looked rather like a dog
• had a series of stripes along its body and tail
• ate an entirely 1 __________ diet
• probably depended mainly on 2 __________ when hunting
• young spent first months of life inside its mother's 3 __________

Decline and extinction
• last evidence in mainland Australia is a 3,100-year-old 4 __________
• probably went extinct in mainland Australia due to animals known as dingoes
• reduction in 5 __________ and available sources of food were partly responsible for decline in Tasmania"""
    p1["groups"][0].pop("renderMode", None)
    p2["groups"][2]["body"] = """23 One advantage of palm oil for manufacturers is that it stays __________ even when not refrigerated.

24 The __________ is the best known of the animals suffering habitat loss as a result of the spread of oil palm plantations.

25 As one of its criteria for the certification of sustainable palm oil, the RSPO insists that growers check __________ on a routine basis.

26 Ellwood and his researchers are looking into whether the bird's nest fern could restore __________ in areas where oil palm trees are grown."""
    p2["groups"][2].pop("renderMode", None)
    p3["paragraphs"][0]["kind"] = "subtitle"
    for par in p3["paragraphs"]:
        if "tenement: a multi-occupancy" in par["text"]:
            par["text"] = "* a tenement: a multi-occupancy building of any sort, but particularly a run-down apartment building or slum building\n** bedrock: the solid, hard rock in the ground that lies under a loose layer of soil"
            par["kind"] = "footnote"
    g = p3["groups"][2]
    g["body"] = """The bedrock myth

In chapter seven, Barr indicates how the lack of bedrock close to the surface does not explain why skyscrapers are absent from 36 __________. He points out that although the cost of foundations increases when bedrock is deep below the surface, this cannot be regarded as 37 __________, especially when compared to 38 __________.

A particularly enjoyable part of the chapter was Barr's account of how foundations are built. He describes not only how 39 __________ are made possible by the use of caissons, but he also discusses their 40 __________. The chapter is well researched but relatively easy to understand."""
    labels = ["development plans", "deep excavations", "great distance", "excessive expense", "impossible tasks", "associated risks", "water level", "specific areas", "total expenditure", "construction guidelines"]
    g["options"] = [{"value": chr(65+i), "label": label} for i, label in enumerate(labels)]
    g.pop("renderMode", None)


def test4(t):
    p1, p2, p3 = t["passages"]
    p1["paragraphs"][0]["kind"] = "subtitle"
    p1["groups"][1]["body"] = """The study carried out by Rocha's team

Aim
• to investigate the feeding habits of bats in farmland near the Ranomafana National Park

Method
• ultrasonic recording to identify favourite feeding spots
• DNA analysis of bat 7 __________

Findings
• the bats
  – were most active in rice fields located on hills
  – ate pests of rice, 8 __________, sugarcane, nuts and fruit
  – prevent the spread of disease by eating 9 __________ and blackflies
• local attitudes to bats are mixed:
  – they provide food rich in 10 __________
  – the buildings where they roost become 11 __________
  – they play an important role in local 12 __________

Recommendation
• farmers should provide special 13 __________ to support the bat population"""
    # Keep the original table layout as a verified illustration, with native answer fields.
    p2["groups"][1]["body"] = """Demographic reconstruction of two German communities

The database that Ogilvie and her team has compiled sheds light on the lives of a range of individuals, as well as those of their 19 __________, over a 300-year period. For example, Ana Regina and Magdalena Riethmüllerin were reprimanded for reading while they should have been paying attention to a 20 __________. There was also Juliana Schweickherdt, who came to the notice of the weavers' guild in the year 1752 for breaking guild rules. As a punishment, she was later given a 21 __________. Cases like this illustrate how the guilds could prevent 22 __________ and stop skilled people from working."""
    p2["groups"][1].pop("renderMode", None)
    p3["groups"][2]["body"] = """How the research was carried out

The researchers started by testing Gareyev's 37 __________; for example, he was required to recall a string of 38 __________ in order and also in reverse order. Although his performance was normal, scans showed an unusual amount of 39 __________ within the areas of Gareyev's brain that are concerned with directing attention. In addition, the scans raised the possibility of unusual strength in the parts of his brain that deal with 40 __________ input."""
    p3["groups"][2].pop("renderMode", None)


def main():
    source = next(ROOT.glob('*/CAMBRIDGE-17/BAN_GOC/*.pdf'))
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    report_path = ROOT / 'library/preparation/cam17-review.json'
    if report_path.exists() and json.loads(report_path.read_text(encoding='utf-8'))['sourceSha256'] != source_hash:
        raise SystemExit('Source PDF changed. Re-review it before applying editorial corrections.')
    records = []
    for n in range(1, 5):
        path = TESTS / f"cam17-test{n}.json"
        t = walk(json.loads(path.read_text(encoding="utf-8")))
        if n == 1:
            test1(t)
        elif n == 2:
            test2(t)
        elif n == 3:
            test3(t)
        elif n == 4:
            test4(t)
        normalize_paragraphs(t)
        t['version'] = '2026-10-21.3'
        t['verification'] = {'status': 'verified', 'note': 'Reading passages and all question blocks compared visually with the supplied scan; paragraph labels, spacing, column order, answer choices and completion text corrected. Original Rocha table retained as a local illustration with native answer fields.', 'report': 'library/preparation/cam17-review.json'}
        content = json.dumps(t, ensure_ascii=False, indent=2)
        path.write_text(content, encoding="utf-8")
        (OVERRIDES / path.name).write_text(content, encoding="utf-8")
        records.append({'id': t['id'], 'sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(), 'passages': 3, 'questions': 40, 'sourcePages': sorted({r['page'] for p in t['passages'] for r in p['sourcePages']}), 'questionReview': 'library/preparation/cam17-questions-review.json'})
    report_path.write_text(json.dumps({'source': str(source.relative_to(ROOT)), 'sourceSha256': source_hash, 'scope': 'Local source fidelity review of all 12 reading passages and 160 question slots, with independent question-image review. This is an editorial review of the supplied edition, not an official IELTS certification.', 'tests': records}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == "__main__":
    main()
