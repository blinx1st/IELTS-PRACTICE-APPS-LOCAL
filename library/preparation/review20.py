"""Editorial corrections following visual review; UTF-8 source avoids PS stdin loss."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]


def save_reviewed(test: dict, report: dict) -> None:
    target = ROOT / f"library/tests/{test['id']}.json"
    test['version'] = max(test.get('version', ''), '2026-10-21.2')
    test['verification'] = {
        'status': 'verified',
        'note': 'All 3 passages and 40 questions, options, instructions and word limits visually reviewed against supplied PDFs; extraction artifacts corrected. The supplied files are retyped documents, not publisher-certified originals.',
        'reviewReport': f"library/preparation/{report['reportFile']}",
    }
    numbers = [q['number'] for p in test['passages'] for g in p['groups'] for q in g['questions']]
    assert numbers == list(range(1, 41)), numbers
    encoded = json.dumps(test, ensure_ascii=False, indent=2) + '\n'
    assert '\ufffd' not in encoded and 'k?k?p?' not in encoded
    assert not re.search(r'\?{3,}', encoded), 'Replacement question marks detected'
    assert not re.search(r'(?:[A-Z0-9]\?[A-Z0-9]|\\n\? )', encoded), 'Corrupted punctuation detected'
    target.write_text(encoded, encoding='utf-8')
    override = ROOT / f"library/preparation/overrides/{test['id']}.json"
    override.parent.mkdir(parents=True, exist_ok=True)
    override.write_text(encoded, encoding='utf-8')
    report['contentSha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    report['encodingCheck'] = 'UTF-8 JSON round-trip; replacement-mark and mojibake checks passed'
    (ROOT / 'library/preparation' / report['reportFile']).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def repair_pilot_encoding() -> None:
    target = ROOT / 'library/tests/cam20-test1.json'
    test = json.loads(target.read_text(encoding='utf-8'))
    for passage in test['passages']:
        for paragraph in passage['paragraphs']:
            paragraph['text'] = re.sub(
                r'[kK][āä][kK][āä]p[ōöőo]',
                lambda m: 'Kākāpō' if m[0][0] == 'K' else 'kākāpō',
                paragraph['text'],
            ).replace('predator- free', 'predator-free')
        for group in passage['groups']:
            for field in ('instructions', 'body'):
                text = group[field].replace('k?k?p?', 'kākāpō')
                text = re.sub(r'(?m)^\? ', '• ', text)
                text = re.sub(r'\?{2,}', '…………….', text)
                text = re.sub(r'([A-Z0-9])\?([A-Z0-9])', r'\1–\2', text)
                text = text.replace(' ? if ', ' — if ')
                group[field] = text
    assert test['passages'][2]['paragraphs'][6]['text'].startswith('When we experience stressful events')
    assert "New Zealand's kākāpō" in test['passages'][0]['groups'][1]['body']
    report_path = ROOT / 'library/preparation/pilot20-review.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    report['reportFile'] = report_path.name
    report['corrections'][0] = 'Normalized corrupted kākāpō diacritics and predator-free spacing.'
    report['encodingCorrection'] = 'Repaired authored Unicode that an earlier Windows PowerShell ASCII stdin pipeline replaced with question marks; saved through this UTF-8 Python source.'
    save_reviewed(test, report)


def repair_pilot_q8() -> None:
    """Repair the shared retyping error in Q8, preserving the source-image evidence."""
    path = ROOT / 'library/tests/cam20-test1.json'
    test = json.loads(path.read_text(encoding='utf-8'))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    notes = test['passages'][0]['groups'][1]
    body = notes['body']
    notes['body'] = re.sub(
        r'nests are created (8\s+[^\n]*?) in where eggs are laid\.',
        r'nests are created in \1 where eggs are laid.', body,
    )
    assert 'nests are created in 8 ' in notes['body']
    assert ' in where eggs are laid.' not in notes['body']
    assert [q['number'] for q in notes['questions']] == list(range(7, 14))
    assert notes['wordLimit'] == 1 and notes['allowNumber'] is True
    test['version'] = max(test['version'], '2026-10-21.3')
    test['verification']['note'] = 'All 3 passages and 40 questions, options, instructions and word limits visually reviewed against supplied PDFs; extraction artifacts and documented source-retyping errors corrected. The supplied files are retyped documents, not publisher-certified originals.'
    report_path = ROOT / 'library/preparation/pilot20-review.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    report['sourceLimitations'] = [
        'Q8 preposition in is misplaced after its blank in both supplied retyped PDFs. The normalized task moves in before blank 8, corroborated by two independent full-question/explanation sources. Original source images remain unchanged.'
        if 'Q8 wording' in entry else entry
        for entry in report['sourceLimitations']
    ]
    correction = 'Moved in before blank 8 in the kakapo notes: nests are created in 8 [blank] where eggs are laid. This repairs a shared source-retyping error; the answer key is unchanged.'
    if correction not in report['corrections']:
        report['corrections'].append(correction)
    report['q8FollowUpReview'] = {
        'date': '2026-10-21',
        'sourcePagesVisuallyChecked': [
            {'source': '80-page Reading-Listening PDF', 'pdfPage': 11},
            {'source': '144-page retyped PDF', 'pdfPage': 9},
            {'source': '144-page retyped PDF continuation', 'pdfPage': 10},
        ],
        'scope': 'Rechecked the whole questions 7-13 note group, every blank and instruction. Only Q8 requires this follow-up repair; all other wording and the ONE WORD AND/OR A NUMBER instruction match the supplied sources.',
        'corroboration': [
            'https://ieltszone.org/practice-tests/reading-test/ielts-20-reading-test-1-online-practice/',
            'https://langgo.edu.vn/cam-20-test-1-reading-passage-1-the-kakapo',
        ],
        'beforeContentSha256': report.get('q8FollowUpReview', {}).get('beforeContentSha256', before),
        'answerKeysChanged': False,
    }
    content = json.dumps(test, ensure_ascii=False, indent=2)
    path.write_text(content, encoding='utf-8')
    (ROOT / 'library/preparation/overrides/cam20-test1.json').write_text(content, encoding='utf-8')
    report['contentSha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Repaired cam20-test1 Q8 preposition; all questions 7-13 visually rechecked.')


def review_test2() -> None:
    path = ROOT / 'library/tests/cam20-test2.json'
    test = json.loads(path.read_text(encoding='utf-8'))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    p1, p2, p3 = test['passages']
    for paragraph in p1['paragraphs']:
        paragraph['text'] = paragraph['text'].replace('seafloor.Manatees', 'seafloor. Manatees')
        paragraph['text'] = paragraph['text'].replace('to 44/130 breathe', 'to breathe')
        paragraph['text'] = paragraph['text'].replace('140,000. Amazonian', '140,000 Amazonian')
    for index, paragraph in enumerate(p2['paragraphs']):
        if index == 0:
            paragraph.pop('label', None)
            if paragraph['text'].startswith('psychologist explains'):
                paragraph['text'] = 'A ' + paragraph['text']
            continue
        m = re.match(r'^([A-F])\.? (.*)$', paragraph['text'])
        if m:
            paragraph['label'], paragraph['text'] = m.groups()
        paragraph['text'] = paragraph['text'].replace(
            'those who study-related misconduct',
            'those who reported procrastinating over their university work were also more likely to engage in study-related misconduct',
        )
    # The source retyping merges what Q38 calls the fifth paragraph.
    merged = next((p for p in p3['paragraphs'] if ' A human, at least, yells back.' in p['text']), None)
    if merged:
        first, second = merged['text'].split(' A human, at least, yells back.', 1)
        index = p3['paragraphs'].index(merged)
        p3['paragraphs'][index:index+1] = [
            {'text': first}, {'text': 'A human, at least, yells back.' + second},
        ]
    for i, paragraph in enumerate(p3['paragraphs'], 1):
        paragraph['id'] = f'p3-para{i}'
    g = p1['groups'][1]
    g['questions'][4]['text'] = 'It is predicted that West Indian manatee populations will fall in the coming decades.'
    g['instructions'] = ('Do the following statements agree with the information given in Reading Passage 1?\n'
        'TRUE — if the statement agrees with the information\n'
        'FALSE — if the statement contradicts the information\n'
        'NOT GIVEN — if there is no information on this')
    g['body'] = ''
    p2['groups'][1]['body'] = p2['groups'][1]['body'].replace('feeling 22,', 'feeling of 22')
    for group, prompt in zip(p2['groups'][2:], [
        'Which TWO comparisons between employees who often procrastinate and those who do not are mentioned in the text?',
        'Which TWO recommendations for getting out of a cycle of procrastination does the writer give?',
    ]):
        group['instructions'] = 'Choose TWO letters, A–E.'
        group['body'] = ''
        for question in group['questions']:
            question['text'] = prompt
    g = p3['groups'][0]
    g['instructions'] = ('Do the following statements agree with the claims of the writer in Reading Passage 3?\n'
        'YES — if the statement agrees with the claims of the writer\n'
        'NO — if the statement contradicts the claims of the writer\n'
        'NOT GIVEN — if it is impossible to say what the writer thinks about this')
    g['body'] = ''
    g['questions'][4]['text'] = "The differing proposals for alterations to the baseball bat led to fierce debate on Sword's team."
    g['questions'][5]['text'] = 'ABS makes changes to the shape of the strike zone feasible.'
    g = p3['groups'][1]
    g['options'] = [{'value':v,'label':label} for v,label in zip('ABCDEFGH', [
        'pitch boundary','numerous disputes','team tactics','subjective assessment',
        'widespread approval','former roles','total silence','perceived area',
    ])]
    g['body'] = g['body'].split('\nA.')[0].strip() + '\n\n' + '\n'.join(
        f"{o['value']}. {o['label']}" for o in g['options'])
    p3['groups'][2]['questions'][0]['options'][0]['label'] = 'It is bound to make key decisions that are wrong.'
    for passage in test['passages']:
        for group in passage['groups']:
            group.pop('renderMode', None)
    assert p3['paragraphs'][4]['text'].startswith('A human, at least, yells back.')
    report = {
        'testId': test['id'], 'reportFile': 'cam20-test2-review.json', 'status': 'verified',
        'beforeContentSha256': before, 'reviewDate': '2026-10-21',
        'method': 'Visual review of all 15 source PDF pages 29–43; compare normalized passages, question statements/options, instructions, limits. Alternate source images 144-page PDF28/29/33/37/38 inspected.',
        'coverage': {'passages':3,'questions':40,'questionGroups':9,'multiGroups':2,
                     'wordLimits':[{'questions':'1-6','wordLimit':1,'allowNumber':True},{'questions':'17-22','wordLimit':1,'allowNumber':False}]},
        'corrections': [
            'Removed printed pagination artifact 44/130, joined seafloor.Manatees spacing and removed stray full stop after 140,000 using alternate source28/29.',
            'Assigned source paragraph labels A-F in Procrastination.',
            'Restored missing question11 and separated questions31/32 after extraction swallowed numbers with no following space.',
            'Restored full A-H phrase option list for questions33-37.',
            'Separated A human paragraph5 from merged paragraph4; this restores source-author paragraph structure and Q38 reference.',
            'Restored missing clause in ProcrastinationD from external excerpt (14 inserted words), corroborated by the original author publication at Durham University.',
            'Added missing of before summary blank22 as grammatical restoration; removed misplaced comma adjacent to blank.',
            'Normalized multi prompt/body so checkbox options appear once; corrected It vs lt in question38 optionA.',
        ],
        'externalCorrections': [{'location':'Procrastination paragraphD',
            'source':'https://ieltszone.org/practice-tests/reading-test/procrastination/',
            'corroboration':'https://dur.ac.uk/research/current/thought-leadership/procrastinating-is-linked-to-health-and-career-problems--but-there-are-things-you-can-do-to-stop/',
            'insertedWords':13},
            {'location':'Robot Umpires paragraph boundary before A human',
             'source':'https://www.newyorker.com/magazine/2021/08/30/invasion-of-the-robot-umpires',
             'operation':'paragraph boundary only; no new text copied'}],
        'sourceLimitations':['Supplied PDFs are retyped; fidelity review includes documented editorial repairs to omissions, not publisher certification. Source images retain original retyping defects.'],
        'unresolvedContentIssues': [],
    }
    save_reviewed(test, report)


def review_test3() -> None:
    path = ROOT / 'library/tests/cam20-test3.json'
    test = json.loads(path.read_text(encoding='utf-8'))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    p1, p2, p3 = test['passages']
    for paragraph in p1['paragraphs']:
        paragraph['text'] = paragraph['text'].replace('Inuit people In 1912', 'Inuit people of Canada. In 1912')
        paragraph['text'] = paragraph['text'].replace('so the mor right', 'so the moment was right')
    for marker in ('The modern frozen food industry began', '1950s families were also looking'):
        merged = next((p for p in p1['paragraphs'] if ' ' + marker in p['text']), None)
        if merged:
            a, b = merged['text'].split(' ' + marker, 1)
            at = p1['paragraphs'].index(merged)
            p1['paragraphs'][at:at+1] = [{'text':a}, {'text':marker+b}]
    for paragraph in p2['paragraphs']:
        m = re.match(r'^([A-F])\. (.*)$', paragraph['text'])
        if m:
            paragraph['label'], paragraph['text'] = m.groups()
    old = p3['paragraphs']
    if old[5]['text'].endswith('within the next'):
        end, richardson = old[6]['text'].split("'Richardson", 1)
        p3['paragraphs'][5:7] = [
            {'text':old[5]['text']+' '+end+"'"},
            {'text':'Richardson'+richardson},
        ]
    for p in test['passages']:
        for i, para in enumerate(p['paragraphs'], 1):
            para['id'] = f"p{p['number']}-para{i}"
    p1['groups'][1]['instructions'] = ('Do the following statements agree with the information given in Reading Passage 1?\n'
        'TRUE — if the statement agrees with the information\nFALSE — if the statement contradicts the information\n'
        'NOT GIVEN — if there is no information on this')
    p1['groups'][1]['body'] = ''
    g = p2['groups'][0]
    g['instructions'] = ('Reading Passage 2 has six sections, A–F.\n'
        'Choose the correct heading for each section from the list of headings below.\n'
        'Write the correct number, i–vii, in boxes 14–19 on your answer sheet.')
    g['body'] = 'List of headings\n\n' + '\n'.join(f"{o['value']}. {o['label']}" for o in g['options'])
    g['body'] += '\n\n' + '\n'.join(f"{q['number']}. {q['text']}" for q in g['questions'])
    for group, prompt in zip(p2['groups'][1:3], [
        'Which TWO of these causes of damage to coral reefs are mentioned by the writer of the text?',
        'Which TWO of the following statements are true of the researchers at London Zoo?',
    ]):
        group['instructions'] = 'Choose TWO letters, A–E.'
        group['body'] = ''
        for question in group['questions']:
            question['text'] = prompt
    p3['groups'][2]['instructions'] = 'Choose the correct letter, A, B, C or D.'
    p3['groups'][2]['body'] = ''
    p3['groups'][2]['questions'][0]['options'][0]['label'] = 'It has grown alongside the development of ever more advanced robots.'
    for passage in test['passages']:
        for group in passage['groups']:
            group.pop('renderMode', None)
    assert p2['paragraphs'][0]['label'] == 'A' and p2['paragraphs'][-1]['label'] == 'F'
    assert p3['paragraphs'][5]['text'].endswith("highly ambitious.'")
    report = {
        'testId':test['id'],'reportFile':'cam20-test3-review.json','status':'verified',
        'beforeContentSha256':before,'reviewDate':'2026-10-21',
        'method':'Visual review of all 13 source PDF pages50–62 against normalized JSON. Alternate144-page source54–56 inspected for Robots and us.',
        'coverage':{'passages':3,'questions':40,'questionGroups':9,'multiGroups':2,
            'wordLimits':[{'questions':'1-7','wordLimit':1},{'questions':'24-26','wordLimit':1}]},
        'corrections':[
            'Restored truncated Frozen Food wording: Inuit people of Canada; moment was right. Each is a short external corroborated repair.',
            'Separated Frozen Food paragraphs beginning The modern frozen food industry and 1950s families.',
            'Assigned source section labels A-F for Coral reefs; preserved second paragraph within sectionD.',
            'Restored Wolpert quote across pages58/59 and separated Richardson response after it.',
            'Restored heading-matching instruction field; normalized multi prompts to avoid duplicated checkbox option lists.',
            'Removed first-question duplication from TFNG/choice instructions and corrected It vs lt in Q37 optionA.',
        ],
        'externalCorrections':[
            {'location':'Frozen Food missing of Canada','source':'https://ieltsdo.com/ielts-reading-test-312/',
             'corroboration':'https://livinghistoryfarm.org/farming-in-the-1950s/farm-life/frozen-foods/','insertedWords':2},
            {'location':'Frozen Food corrupted mor -> moment was','source':'https://practicepteonline.com/ielts-reading-test-312/','replacementWords':2},
        ],
        'sourceLimitations':['Retyped source fidelity with documented short editorial repairs, not publisher certification. Source image preserves original truncation.'],
        'unresolvedContentIssues':[],
    }
    save_reviewed(test, report)


def review_test4() -> None:
    path = ROOT / 'library/tests/cam20-test4.json'
    test = json.loads(path.read_text(encoding='utf-8'))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    p1, p2, p3 = test['passages']
    for paragraph in p1['paragraphs']:
        paragraph['text'] = re.sub(r'her sun.+? at Ghost Ranch', 'her summer retreat at Ghost Ranch', paragraph['text'])
    merged = next((p for p in p1['paragraphs'] if " O'Keeffe eventually owned" in p['text']), None)
    if merged:
        a, b = merged['text'].split(" O'Keeffe eventually owned", 1)
        at = p1['paragraphs'].index(merged)
        p1['paragraphs'][at:at+1] = [{'text':a}, {'text':"O'Keeffe eventually owned"+b}]
    merged = next((p for p in p2['paragraphs'] if ' D. As the floodwaters rose' in p['text']), None)
    if merged:
        a, b = merged['text'].split(' D. As the floodwaters rose', 1)
        a += " processes and that engage and benefit communities and local decision-makers.'"
        at = p2['paragraphs'].index(merged)
        p2['paragraphs'][at:at+1] = [{'text':a}, {'text':'D. As the floodwaters rose'+b}]
    for paragraph in p2['paragraphs']:
        paragraph['text'] = paragraph['text'].replace('installation or a', 'installation of a')
    for paragraph in p3['paragraphs']:
        paragraph['text'] = paragraph['text'].replace('on duty in vai the world', 'on duty in various parts of the world')
    for passage in (p2, p3):
        for paragraph in passage['paragraphs']:
            m = re.match(r'^([A-G])\. (.*)$', paragraph['text'])
            if m:
                paragraph['label'], paragraph['text'] = m.groups()
    for passage in test['passages']:
        for i, paragraph in enumerate(passage['paragraphs'], 1):
            paragraph['id'] = f"p{passage['number']}-para{i}"
        for group in passage['groups']:
            group.pop('renderMode', None)
    p1['groups'][0]['body'] = ("The life and work of Georgia O'Keeffe\n\n"
        '• studied art, then worked as a 1 ……………… in various places in the USA\n'
        '• created drawings using 2 ……………… which were exhibited in New York City\n'
        "• moved to New York and became famous for her paintings of the city's 3 ………………\n"
        '• produced a series of innovative close-up paintings of 4 ………………\n'
        '• went to New Mexico and was initially inspired to paint the many 5 ……………… that could be found there\n'
        '• continued to paint various features that together formed the dramatic 6 ……………… of New Mexico for over forty years\n'
        '• travelled widely by plane in later years, and painted pictures of clouds and 7 ……………… seen from above')
    p1['groups'][1]['instructions'] = ('Do the following statements agree with the information given in Reading Passage 1?\n'
        'TRUE — if the statement agrees with the information\nFALSE — if the statement contradicts the information\n'
        'NOT GIVEN — if there is no information on this')
    p1['groups'][1]['body'] = ''
    assert [p.get('label') for p in p2['paragraphs']] == list('ABCDEF')
    assert [p.get('label') for p in p3['paragraphs'][1:]] == list('ABCDEFG')
    assert all(g.get('wordLimit') == 1 for pas in test['passages'] for g in pas['groups'] if g['type']=='completion')
    report = {
        'testId':test['id'],'reportFile':'cam20-test4-review.json','status':'verified',
        'beforeContentSha256':before,'reviewDate':'2026-10-21',
        'method':'Visual review of all13 source80-page PDFpages68–80; alternate144-page source68/71/75 visually inspected.',
        'coverage':{'passages':3,'questions':40,'questionGroups':8,
            'wordLimits':[{'questions':'1-7','wordLimit':1},{'questions':'18-22','wordLimit':1},{'questions':'37-40','wordLimit':1}]},
        'corrections':[
            'Restored corrupted summer retreat wording from the original Metropolitan Museum of Art essay; separated paragraph beginning O’Keeffe eventually owned.',
            'Separated missing sectionD from sectionC, retained its page continuation, assigned allA–F labels in climate-change passage.',
            'Restored omitted final ten words of Susanna Tol quotation from original Geographical article; this clause supplies evidence for question23.',
            'Restored guard dogs in various parts of the world from alternate supplied PDF75; assigned A–G section labels.',
            'Corrected installation or a -> installation of a as grammatical typo; normalized notes bullet continuation around blanks5/6.',
            'Removed first question duplication from TFNG instructions. All matching options verified against sourceimages.',
        ],
        'externalCorrections':[
            {'location':'Georgia O’Keeffe corrupted summer retreat',
             'source':'https://www.metmuseum.org/essays/georgia-okeeffe-1887-1986','replacementWords':2},
            {'location':'Climate change paragraphC omitted end of quotation',
             'source':'https://geographical.co.uk/climate-change/adapting-to-climate-change','insertedWords':10},
        ],
        'sourceLimitations':['Retyped source fidelity plus documented brief editorial repairs, not publisher certification. Sourceimages retain original textual omissions.'],
        'unresolvedContentIssues':[],
    }
    save_reviewed(test, report)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'pilot-q8':
        repair_pilot_q8()
    elif len(sys.argv) > 1 and sys.argv[1] == 'test4':
        review_test4()
    elif len(sys.argv) > 1 and sys.argv[1] == 'test3':
        review_test3()
    elif len(sys.argv) > 1 and sys.argv[1] == 'test2':
        review_test2()
    else:
        repair_pilot_encoding()
