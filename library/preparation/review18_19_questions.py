"""Question-field corrections from complete visual review of supplied scans.

Only passage.groups is edited; reading text, source-page records and assets stay intact.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / 'library/tests'
OVERRIDES = ROOT / 'library/preparation/overrides'


def clean(text):
    replacements = {
        'ANDIOR': 'AND/OR', 'NOT GIVEN_': 'NOT GIVEN',
        'ofpeople': 'of people', 'ofphrases': 'of phrases', 'claimsofthe': 'claims of the',
        'areference': 'a reference', 'adescription': 'a description',
        'acomparison': 'a comparison', 'Arecommendation': 'A recommendation',
        'Aperiod': 'A period', 'Apossible': 'A possible',
        'beena': 'been a', 'howa ': 'how a ', 'Ithas': 'It has',
        'avery ': 'a very ', 'itis ': 'It is ', 'Itis ': 'It is ',
        'Inthe ': 'In the ', 'howscientists': 'how scientists',
        'nota ': 'not a ', 'Hekepta': 'He kept a', 'Someofthe': 'Some of the',
        'tocompare': 'to compare', 'toillustrate': 'to illustrate',
        'alonger': 'a longer', 'alarge': 'a large',
        'amention': 'a mention', 'aregular': 'a regular', 'acommunity': 'a community',
        'Atthe': 'At the', 'Achange': 'A change', 'arough': 'a rough', 'Amove': 'A move',
        'resuIts': 'results',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\bltis\b', 'It is', text)
    text = re.sub(r'\blts\b', 'Its', text)
    text = re.sub(r'\s*(?:\d+\s+)?[>/|@=+\-30 ]*p\.\s*1[12]\d.*$', '', text, flags=re.S)
    return text.strip()


def questions(test):
    return {q['number']: q for p in test['passages'] for g in p['groups'] for q in g['questions']}


def group(test, passage, index):
    return test['passages'][passage - 1]['groups'][index - 1]


def option(test, number, letter, label):
    q = questions(test)[number]
    next(o for o in q['options'] if o['value'] == letter)['label'] = label


def shared_option(g, letter, label):
    next(o for o in g['options'] if o['value'] == letter)['label'] = label


def multi_prompt(g, prompt):
    for q in g['questions']:
        q['text'] = prompt
    g['body'] = ''


def common(test):
    for p in test['passages']:
        for g in p['groups']:
            g['instructions'] = clean(g.get('instructions', ''))
            for q in g['questions']:
                q['text'] = clean(q.get('text', ''))
                q['text'] = re.sub(r'^[~_=—]+\s*', '', q['text'])
                for o in q.get('options', []):
                    o['label'] = clean(o['label'])
                    o['label'] = re.sub(r'^[~_=—]+\s*', '', o['label'])
            for o in g.get('options', []):
                o['label'] = clean(o['label'])
                o['label'] = re.sub(r'^[~_=—]+\s*', '', o['label'])
            if g.get('renderMode') == 'source':
                for q in g['questions']:
                    q['text'] = ''


def cam18_test1(test):
    q = questions(test)
    for number, text in {
        15: 'reference to the aspects of any tree that contribute to its worth',
        16: 'mention of the potential use of wood to help run vehicles',
        17: 'examples of insects that attack trees',
        18: 'an alternative name for trees that produce low-use wood',
    }.items():
        q[number]['text'] = text


def cam18_test2(test):
    g = group(test, 2, 1)
    g['instructions'] = 'Choose the correct letter, A, B, C or D.\nWrite the correct letter in boxes 14–19 on your answer sheet.'
    q = questions(test)
    q[17]['text'] = 'What challenge does the writer refer to in the fourth paragraph?'
    option(test, 19, 'D', 'Human shortcomings will make creating the machines we need more difficult.')
    shared_option(group(test, 2, 3), 'F', 'technology experts')
    for p in test['passages']:
        for g in p['groups']:
            g['body'] = re.sub(r'\bAl\b', 'AI', g.get('body', ''))
            for item in [*g['questions'], *g.get('options', [])]:
                for field in ('text', 'label'):
                    if field in item:
                        item[field] = re.sub(r'\bAl\b', 'AI', item[field])
                for o in item.get('options', []):
                    o['label'] = re.sub(r'\bAl\b', 'AI', o['label'])


def cam18_test3(test):
    q = questions(test)
    q[1]['text'] = 'an explanation of the industrial processes that create potential raw materials for concrete'
    q[2]['text'] = 'a reference to the various locations where high-rise wooden buildings can be found'
    q[4]['text'] = 'the belief that more high-rise wooden buildings are needed before wood can be regarded as a viable construction material'
    shared_option(group(test, 1, 3), 'B', 'Markus Mannström')
    group(test, 2, 1)['instructions'] = 'Reading Passage 2 has seven paragraphs, A–G.\nChoose the correct heading for each paragraph from the list of headings below.\nWrite the correct number, i–viii, in boxes 14–20 on your answer sheet.'
    option(test, 28, 'A', 'It has a very broad appeal.')
    option(test, 28, 'C', 'It is relatively simple to implement.')
    option(test, 30, 'C', 'the assistance given to a student in their initial stages of learning')


def cam18_test4(test):
    q = questions(test)
    g = group(test, 1, 3)
    multi_prompt(g, 'Which TWO advantages of using newer buildings for green roofs are mentioned in Paragraph C of the passage?')
    shared_option(g, 'A', 'a longer growing season for edible produce')
    shared_option(g, 'E', 'a large surface area for growing plants')
    g = group(test, 1, 4)
    multi_prompt(g, 'Which TWO aims of new variations on the concept of green roofs are mentioned in Paragraph E of the passage?')
    shared_option(g, 'E', 'to collect water to supply other buildings')
    group(test, 2, 1)['instructions'] = 'Choose the correct letter, A, B, C or D.\nWrite the correct letter in boxes 14–16 on your answer sheet.'
    shared_option(group(test, 3, 2), 'H', 'hazardous exploration')
    shared_option(group(test, 3, 2), 'I', 'biographer’s perspective')
    shared_option(group(test, 3, 2), 'J', 'narrow investigation')
    q[40]['text'] = 'What is Greene’s main point in the final paragraph?'


def cam19_test1(test):
    multi_prompt(group(test, 2, 2), 'Which TWO of the following statements does the writer make about inhabitants of the Mediterranean region in the ancient world?')
    g = group(test, 2, 3)
    multi_prompt(g, 'Which TWO of the following statements does the writer make about piracy and ancient Greece?')
    shared_option(g, 'B', 'Attitudes towards piracy changed shortly after the Iliad and the Odyssey were written.')


def cam19_test2(test):
    multi_prompt(group(test, 2, 3), 'Which TWO facts about Emma Raducanu’s withdrawal from the Wimbledon tournament are mentioned in the text?')
    multi_prompt(group(test, 2, 4), 'Which TWO facts about anxiety are mentioned in Paragraph E of the text?')
    shared_option(group(test, 3, 1), 'H', 'unique')
    shared_option(group(test, 3, 1), 'J', 'satisfaction')


def cam19_test3(test):
    q = questions(test)
    for number, text in {
        27: 'What does the reader learn about the conversation in the first paragraph?',
        28: 'What assists the electronic translator during lectures at Karlsruhe Institute of Technology?',
        29: 'When referring to The Hitchhiker’s Guide to the Galaxy, the writer suggests that',
        30: 'What does the writer say about sharing earpieces?',
        34: 'Users may be able to maintain their local customs',
    }.items():
        q[number]['text'] = text
    g = group(test, 3, 2)
    g['instructions'] = 'Complete each sentence with the correct ending, A–F, below.\nWrite the correct letter, A–F, in boxes 31–34 on your answer sheet.'
    shared_option(g, 'A', 'but there are concerns about this.')


def cam19_test4(test):
    q = questions(test)
    group(test, 2, 3)['allowNumber'] = False
    q[28]['text'] = 'What point is made about Richard Dawkins’ book The Selfish Gene?'


def finish_native_bodies(test):
    for p in test['passages']:
        for g in p['groups']:
            if g.get('renderMode') == 'source':
                continue
            if g['type'] == 'matching':
                assert all(q.get('text', '').strip() for q in g['questions']), g['id']
                g['body'] = '\n\n'.join(f"{q['number']}. {q['text']}" for q in g['questions'])
                if any(o['label'] != o['value'] for o in g.get('options', [])):
                    choices = '\n'.join(f"{o['value']}. {o['label']}" for o in g['options'])
                    g['body'] = choices + '\n\n' + g['body']
            elif g['type'] in ('choice', 'tfng', 'ynng'):
                assert all(q.get('text', '').strip() for q in g['questions']), g['id']
                g['body'] = ''


def reading_snapshot(test):
    return [{k: v for k, v in p.items() if k != 'groups'} for p in test['passages']]


def apply_book(book):
    for n in range(1, 5):
        path = TESTS / f'cam{book}-test{n}.json'
        test = json.loads(path.read_text(encoding='utf-8'))
        before = copy.deepcopy(reading_snapshot(test))
        common(test)
        globals()[f'cam{book}_test{n}'](test)
        finish_native_bodies(test)
        assert before == reading_snapshot(test), 'Reading fields changed'
        numbers = [q['number'] for p in test['passages'] for g in p['groups'] for q in g['questions']]
        assert sorted(numbers) == list(range(1, 41)), (test['id'], numbers)
        test['version'] = max(str(test.get('version', '')), '2026-10-21.4')
        test['verification']['questionsReport'] = 'library/preparation/cam18-19-questions-review.json'
        text = json.dumps(test, ensure_ascii=False, indent=2)
        assert '\ufffd' not in text
        path.write_text(text, encoding='utf-8')
        (OVERRIDES / path.name).write_text(text, encoding='utf-8')
        print(test['id'], len(numbers), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    apply_book(int(sys.argv[1]))
