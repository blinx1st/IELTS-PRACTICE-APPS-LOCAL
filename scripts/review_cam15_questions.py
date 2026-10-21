"""Source-image review corrections for all 160 Cambridge 15 question slots.

Run after prepare_library.py assemble. Keep the resulting full overrides.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def body(g, text, source=False):
    g['body'] = text.strip()
    if source:
        g['renderMode'] = 'source'
    else:
        g.pop('renderMode', None)
    for q in g['questions']:
        q['text'] = ''


def options(g, labels):
    g['options'] = [{'value': chr(65 + i), 'label': label} for i, label in enumerate(labels)]


def clean(s):
    for old, new in {'asuggestion': 'a suggestion', 'areference': 'a reference', 'Aspecies': 'A species', 'Areduction': 'A reduction', 'Hecompared': 'He compared', 'Hecontrasted': 'He contrasted', 'Onleaving': 'On leaving', 'Schoo!': 'School', 'Inthe': 'In the', 'overa': 'over a', 'makea': 'make a', 'canonly': 'can only', 'Afast-food': 'A fast-food', 'Itis': 'It is', 'lt would': 'It would', 'irom the passage': 'from the passage', 'letfer': 'letter'}.items():
        s = s.replace(old, new)
    s = re.sub(r'\s*[|:]+\s*$', '', s)
    s = re.sub(r"\s*['| I]*Reading\s*$", '', s)
    s = re.sub(r'\s*[|:]+\s*$', '', s)
    s = re.sub(r'\s*[>/~\d| @]*@?\s*p\.\s*12\d.*$', '', s)
    return re.sub(r'^[+~=_]+\s*', '', s).strip()


def normalize(t):
    for p in t['passages']:
        for g in p['groups']:
            lo, hi = g['questions'][0]['number'], g['questions'][-1]['number']
            g['heading'] = f'Question {lo}' if lo == hi else f'Questions {lo}–{hi}'
            if g.get('wordLimit'):
                g['allowNumber'] = False
                if g['type'] == 'completion':
                    intro = 'Complete the table below.' if (t['test'], lo) in [(1, 8), (4, 6)] else 'Complete the notes below.' if (t['test'], lo) in [(1, 1), (3, 8), (4, 1), (4, 20)] else 'Complete the summary below.'
                    limit = 'ONE WORD ONLY' if g['wordLimit'] == 1 else 'NO MORE THAN TWO WORDS'
                    g['instructions'] = f'{intro}\nChoose {limit} from the passage for each answer.\nWrite your answers in boxes {lo}–{hi} on your answer sheet.'
            if g['type'] == 'multi':
                g['instructions'] = f'Choose TWO letters, A–E.\nWrite the correct letters in boxes {lo} and {hi} on your answer sheet.'
            if g['type'] in ('tfng', 'ynng'):
                tf = g['type'] == 'tfng'
                g['instructions'] = f"Do the following statements agree with the {'information given' if tf else 'claims of the writer'} in Reading Passage {p['number']}?\nIn boxes {lo}–{hi} on your answer sheet, write:\n" + ('TRUE — if the statement agrees with the information\nFALSE — if the statement contradicts the information\nNOT GIVEN — if there is no information on this' if tf else 'YES — if the statement agrees with the claims of the writer\nNO — if the statement contradicts the claims of the writer\nNOT GIVEN — if it is impossible to say what the writer thinks about this')
            g['instructions'] = clean(g['instructions'])
            for q in g['questions']:
                q['text'] = clean(q['text'])
                if q.get('options'):
                    q['text'] = re.split(r'\s+A[_—~ -]+\s*', q['text'], maxsplit=1)[0].strip()
                for op in q.get('options', []):
                    op['label'] = clean(op['label'])
            for op in g.get('options', []):
                op['label'] = clean(op['label'])
            if g['type'] == 'matching' and all(q['text'] for q in g['questions']):
                g['body'] = ''  # Question stems and options are rendered natively.
            if g['type'] in ('tfng', 'ynng', 'choice'):
                g['body'] = '\n'.join(f"{q['number']} {q['text']}" for q in g['questions'])


def test1(t):
    a, b, c = [p['groups'] for p in t['passages']]
    body(a[0], '''The nutmeg tree and fruit
• the leaves of the tree are 1 __________ in shape
• the 2 __________ surrounds the fruit and breaks open when the fruit is ripe
• the 3 __________ is used to produce the spice nutmeg
• the covering known as the aril is used to produce 4 __________
• the tree has yellow flowers and fruit''')
    a[1]['questions'][-1]['text'] = 'Following the Treaty of Breda, the Dutch had control of all the islands where nutmeg grew.'
    # Original chronology table preserved, with native answer boxes below it.
    body(a[2], '''Middle Ages: Nutmeg was brought to Europe by the 8 __________.
16th century: European nations took control of the nutmeg trade.
17th century: Demand grew, as nutmeg was believed to be effective against the disease known as the 9 __________.
The Dutch took control of the Banda Islands, restricted production to a few areas, put 10 __________ on nutmeg to avoid cultivation outside the islands, and finally obtained the island of 11 __________ from the British.
Late 18th century: In 1770, nutmeg plants were secretly taken to 12 __________. In 1778, half the Banda Islands' nutmeg plantations were destroyed by a 13 __________.''', source=True)
    body(b[1], '''The impact of driverless cars

Figures from the Transport Research Laboratory indicate that most motor accidents are partly due to 19 __________, so the introduction of driverless vehicles will result in greater safety. In addition to the direct benefits of automation, it may bring other advantages. For example, schemes for 20 __________ will be more workable, especially in towns and cities, resulting in fewer cars on the road.

According to the University of Michigan Transportation Research Institute, there could be a 43 percent drop in 21 __________ of cars. However, this would mean that the yearly 22 __________ of each car would, on average, be twice as high as it currently is. This would lead to a higher turnover of vehicles, and therefore no reduction in automotive manufacturing.''')
    b[2]['body'] = 'Which TWO benefits of automated vehicles does the writer mention?'
    options(b[2], ['Car travellers could enjoy considerable cost savings.', 'It would be easier to find parking spaces in urban areas.', 'Travellers could spend journeys doing something other than driving.', 'People who find driving physically difficult could travel independently.', 'A reduction in the number of cars would mean a reduction in pollution.'])
    b[3]['body'] = 'Which TWO challenges to automated vehicle development does the writer mention?'
    options(b[3], ['making sure the general public has confidence in automated vehicles', 'managing the pace of the transition from conventional to automated vehicles', 'deciding how to compensate professional drivers who become redundant', 'setting up the infrastructure to make roads suitable for automated vehicles', 'getting automated vehicles to adapt to various different driving conditions'])
    options(c[1], ['Peter Fleming', 'Ran Fiennes', 'Chris Bonington', 'Robin Hanbury-Tenison', 'Wilfred Thesiger'])
    body(c[2], '''The writer's own bias

The writer has experience of a large number of 38 __________, and was the first stranger that certain previously 39 __________ people had encountered. He believes there is no need for further exploration of Earth's 40 __________, except to answer specific questions such as how buffalo eat.''')


def test2(t):
    a, b, c = [p['groups'] for p in t['passages']]
    body(a[1], '''Guard rails

Guard rails were introduced on British roads to improve the 7 __________ of pedestrians, while ensuring that the movement of 8 __________ is not disrupted. Pedestrians are led to access points, and encouraged to cross one 9 __________ at a time.

An unintended effect is to create psychological difficulties in crossing the road, particularly for less 10 __________ people. Another result is that some people cross the road in a 11 __________ way. The guard rails separate 12 __________, and make it more difficult to introduce forms of transport that are 13 __________.''')
    body(b[1], '''The woolly mammoth revival project

Professor George Church and his team are trying to identify the 18 __________ which enabled mammoths to live in the tundra. The findings could help preserve the mammoth's close relative, the endangered Asian elephant.

According to Church, introducing Asian elephants to the tundra would involve certain physical adaptations to minimise 19 __________. To survive in the tundra, the species would need to have the mammoth-like features of thicker hair, 20 __________ of a reduced size and more 21 __________.

Repopulating the tundra with mammoths or Asian elephant/mammoth hybrids would also have an impact on the environment, which could help to reduce temperatures and decrease 22 __________.''')
    b[2]['instructions'] = 'Look at the following statements (Questions 23–26) and the list of people below.\nMatch each statement with the correct person, A, B or C.\nWrite the correct letter, A, B or C, in boxes 23–26 on your answer sheet.\nNB You may use any letter more than once.'
    options(b[2], ['Ben Novak', 'Michael Archer', 'Beth Shapiro'])
    b[2]['questions'][0]['text'] = 'Reintroducing an extinct species to its original habitat could improve the health of a particular species living there.'
    b[2]['body'] = ''
    c[0]['questions'][-1]['options'][0]['label'] = 'It is clear whether a dominant laugh is produced by a high- or low-status person.'
    body(c[1], '''The benefits of humour

In one study at Australian National University, randomly chosen groups of participants were shown one of three videos, each designed to generate a different kind of 32 __________. When all participants were then given a deliberately frustrating task to do, it was found that those who had watched the 33 __________ video persisted with the task for longer and tried harder to accomplish the task than either of the other two groups.

A second study in which participants were asked to perform a particularly 34 __________ task produced similar results. According to researchers David Cheng and Lu Wang, these findings suggest that humour not only reduces 35 __________ and helps build social connections but it may also have a 36 __________ effect on the body and mind.''')
    options(c[1], ['laughter', 'relaxing', 'boring', 'anxiety', 'stimulating', 'emotion', 'enjoyment', 'amusing'])


def test3(t):
    a, b, c = [p['groups'] for p in t['passages']]
    a[1]['instructions'] = 'Complete the notes below.\nChoose ONE WORD ONLY from the passage for each answer.\nWrite your answers in boxes 8–13 on your answer sheet.'
    body(a[1], '''Moore's career as an artist

1930s
• Moore's exhibition at the Leicester Galleries is criticised by the press
• Moore is urged to offer his 8 __________ and leave the Royal College

1940s
• Moore turns to drawing because 9 __________ for sculpting are not readily available
• While visiting his hometown, Moore does some drawings of 10 __________
• Moore is employed to produce a sculpture of a 11 __________
• 12 __________ start to buy Moore's work
• Moore's increased 13 __________ makes it possible for him to do more ambitious sculptures

1950s
• Moore's series of bronze figures marks a further change in his style''')
    body(b[1], '''How the Desolenator works

The energy required to operate the Desolenator comes from sunlight. The device can be used in different locations, as it has 21 __________. Water is fed into a pipe, and a 22 __________ of water flows over a solar panel. The water then enters a boiler, where it turns into steam. Any particles in the water are caught in a 23 __________. The purified water comes out through one tube, and all types of 24 __________ come out through another. A screen displays the 25 __________ of the device, and transmits the information to the company so that they know when the Desolenator requires 26 __________.''')
    c[0]['questions'][-1]['text'] = 'All the fairy tales analysed by Tehrani'
    c[0]['body'] = ''
    options(c[0], ['may be provided through methods used in biological research.', 'are the reason for their survival.', 'show considerable global variation.', 'contain animals which transform to become humans.', 'were originally spoken rather than written.', 'have been developed without factual basis.'])
    body(c[1], '''Phylogenetic analysis of Little Red Riding Hood

Tehrani used techniques from evolutionary biology to find out if 32 __________ existed among 58 stories from around the world. He also wanted to know which aspects of the stories had fewest 33 __________, as he believed these aspects would be the most important ones. Contrary to other beliefs, he found that some 34 __________ that were included in a story tended to change over time, and that the middle of a story seemed no more important than the other parts. He was also surprised that parts of a story which seemed to provide some sort of 35 __________ were unimportant. The aspect that he found most important in a story's survival was 36 __________.''')
    options(c[1], ['ending', 'events', 'warning', 'links', 'records', 'variations', 'horror', 'people', 'plot'])
    for par in t['passages'][1]['paragraphs']:
        par['text'] = par['text'].replace('so it is a really bad situation,’', 'so it is a really bad situation.’')
    for par in t['passages'][2]['paragraphs']:
        par['text'] = par['text'].replace('survival-relevant information in it, says anthropologist', 'survival-relevant information in it,’ says anthropologist')


def test4(t):
    a, b, c = [p['groups'] for p in t['passages']]
    body(a[0], '''The importance of the huarango tree

• its roots can extend as far as 80 metres into the soil
• can access 1 __________ deep below the surface
• was a crucial part of local inhabitants' 2 __________ a long time ago
• helped people to survive periods of 3 __________
• prevents 4 __________ of the soil
• prevents land from becoming a 5 __________''')
    body(a[1], '''Traditional uses of the huarango tree
Part of tree — Traditional use
6 __________ — fuel
7 __________ and __________ — medicine
8 __________ — construction''', source=True)
    a[2]['questions'][-1]['text'] = 'Whaley has plans to go to Africa to set up a similar project.'
    b[0]['questions'][-1]['text'] = 'The children of Gomera now learn Silbo.'
    b[1]['instructions'] = 'Complete the notes below.\nChoose ONE WORD ONLY from the passage for each answer.\nWrite your answers in boxes 20–26 on your answer sheet.'
    body(b[1], '''Silbo Gomero

How Silbo is produced
• high- and low-frequency tones represent different sounds in Spanish 20 __________
• pitch of whistle is controlled using silbador's 21 __________
• 22 __________ is changed with a cupped hand

How Silbo is used
• has long been used by shepherds and people living in secluded locations
• in everyday use for the transmission of brief 23 __________
• can relay essential information quickly, e.g. to inform people about 24 __________

The future of Silbo
• future under threat because of new 25 __________
• Canaries' authorities hoping to receive a UNESCO 26 __________ to help preserve it''')
    # The supplied page says A–J but actually prints nine options, A–I.
    body(c[0], '''Big businesses

Many big businesses today are prepared to harm people and the environment in order to make money, and they appear to have no 27 __________. Lack of 28 __________ by governments and lack of public 29 __________ can lead to environmental problems such as 30 __________ or the destruction of 31 __________.''')
    options(c[0], ['funding', 'trees', 'rare species', 'moral standards', 'control', 'involvement', 'flooding', 'overfishing', 'worker support'])
    c[1]['questions'][-1]['text'] = 'What pressure was exerted by big business in the case of the disease BSE?'


def main():
    source = next(ROOT.glob('*/CAMBRIDGE-15/BAN_GOC/*.pdf'))
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    report_path = ROOT / 'library/preparation/cam15-questions-review.json'
    if report_path.exists():
        assert json.loads(report_path.read_text(encoding='utf-8'))['sourceSha256'] == source_hash, 'Source changed: review required.'
    records = []
    for n in range(1, 5):
        path = ROOT / f'library/tests/cam15-test{n}.json'
        t = json.loads(path.read_text(encoding='utf-8'))
        [test1, test2, test3, test4][n-1](t)
        normalize(t)
        t['version'] = '2026-10-21.3'
        t['verification'] = {'status': 'verified', 'note': 'All 12 reading passages and 160 question slots compared with the supplied scan. Completion text, options, limits and question numbering corrected. Two original table layouts retained with native answer fields.', 'report': 'library/preparation/cam15-questions-review.json'}
        content = json.dumps(t, ensure_ascii=False, indent=2)
        path.write_text(content, encoding='utf-8')
        (ROOT / 'library/preparation/overrides' / path.name).write_text(content, encoding='utf-8')
        records.append({'id': t['id'], 'questions': 40, 'sha256': hashlib.sha256(content.encode()).hexdigest(), 'sourceQuestionPages': [[20,21,24,25,28,29], [41,44,45,48,49,50], [62,63,64,67,70,71,72], [84,85,88,89,92,93,94]][n-1]})
    report_path.write_text(json.dumps({'source': str(source.relative_to(ROOT)), 'sourceSha256': source_hash, 'scope': 'Visual review of every question, option, word limit and retained source table; reading review in reading-review/cam15-*.jpg. A–J typo on test 4 summary retained as supplied; nine actual choices A–I are available.', 'tests': records}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
