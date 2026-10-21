"""Reproducible transcription of local Cambridge Reading keys.

Every entry was read against the rendered source PDF key page. OCR is an
inspection aid only. Running the script writes private, server-side key files.
Use --render to regenerate source PNG/OCR inspection evidence (PyMuPDF).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {13: [117,119,121,123], 14: [120,122,124,126],
         15: [122,124,126,128], 17: [113,115,117,119],
         18: [122,124,126,128], 19: [120,122,124,126],
         20: [126,127,128,129]}
# A vertical bar separates question numbers; a tilde separates alternatives.
# NG expands to NOT GIVEN. Roman numerals intentionally remain lower-case.
DATA = {
 'cam13-test1': 'update|environment|captain|films|season|accommodation|blog|FALSE|NG|FALSE|TRUE|NG|TRUE|iv|vi|i|v|viii|iii|E|B|D|A|focus|pleasure|curiosity|B|C|C|D|A|D|A|E|C|G|B|YES|NG|NO',
 'cam13-test2': 'oils|friendship|funerals|wealth|indigestion|India|camels|Alexandria|Venice|TRUE|FALSE|NG|FALSE|B|F|B|E|A|B|C|animals|childbirth|placebo|game|strangers|names|D|C|A|D|D|D|C|B|A|C|A|B|C|D',
 'cam13-test3': 'furniture|sugar|ropes|charcoal|bowls|hormones|cosmetics|dynamite|FALSE|FALSE|NG|TRUE|NG|B|C|A|B|recording devices|fathers~dads|bridge hypothesis|repertoire|vests~audio-recording vests|vocabulary|F|A|E|C|H|A|B|D|shells|lake|rainfall|grains|pottery|B|A|D|A',
 'cam13-test4': 'FALSE|FALSE|TRUE|TRUE|FALSE|TRUE|NG|TRUE|wool|navigator|gale|training|fire|minerals|carbon|water|agriculture|C|E|A|D|E|C|F|G|F|D|A|B|F|B|G|E|A|YES|NG|NO|NG|YES|NO',
 'cam14-test1': 'creativity|rules|cities|traffic|crime|competition|evidence|life|TRUE|TRUE|NG|FALSE|TRUE|E|C|F|C|A|B|D|D|E|activists|consumerism|leaflets|police|E|D|B|D|C|YES|NO|NO|NG|restaurants|performance|turnover|goals|characteristics',
 'cam14-test2': 'FALSE|TRUE|NG|FALSE|NG|TRUE|FALSE|TRUE|merchant|equipment|gifts|canoe|mountains|F|C|E|D|B|design~designs|pathogens|tuberculosis|wards|communal|public|miasmas|cholera|vi|i|iii|ii|ix|vii|iv|viii|productive|perfectionists|dissatisfied|TRUE|FALSE|NG',
 'cam14-test3': 'B|A|D|NG|NO|YES|B|C|B|A|A|C|A|C|H|A|F|I|B|E|B|C|ecology|prey|habitats|antibiotics|B|G|F|E|C|NO|YES|NG|NO|YES|encouraging|desire|autonomy|targeted',
 'cam14-test4': 'four~4|young|food|light|aggressively|location|neurons|chemicals|FALSE|TRUE|FALSE|NG|TRUE|B|E|C|A|TRUE|TRUE|NG|FALSE|NG|B|D|B|E|FALSE|NG|FALSE|TRUE|FALSE|TRUE|NG|large|microplastic|populations|concentrations|predators|disasters|A',
 'cam15-test1': 'oval|husk|seed|mace|FALSE|NG|TRUE|Arabs|plague|lime|Run|Mauritius|tsunami|C|B|E|G|D|human error|car sharing~car-sharing|ownership|mileage|C|D|A|E|A|C|C|D|A|B|E|A|D|E|B|expeditions~unique expeditions|uncontacted~isolated|surface~land surface',
 'cam15-test2': 'B|C|F|D|E|A|safety|traffic|carriageway|mobile|dangerous|communities|healthy|F|A|D|A|genetic traits|heat loss|ears|fat~insulating fat|emissions~carbon emissions|B|C|A|C|C|A|B|B|D|F|H|C|D|E|NG|YES|NO|NO',
 'cam15-test3': 'TRUE|FALSE|NG|TRUE|NG|FALSE|TRUE|resignation|materials|miners|family|collectors|income|iii|vi|v|x|iv|viii|i|wheels|film|filter|waste|performance|servicing|C|B|F|A|E|D|F|B|C|G|B|D|A|A',
 'cam15-test4': 'water|diet|drought|erosion|desert|branches~its branches~huarango branches~the branches|leaves bark~bark leaves|trunk~its trunk~huarango trunk~the trunk|NG|FALSE|TRUE|FALSE|NG|NG|FALSE|TRUE|FALSE|FALSE|TRUE|words|finger|direction|commands|fires|technology|award|D|E|F|H|B|C|D|B|YES|NG|NO|YES|NG|D',
 'cam17-test1': 'population|suburbs|businessmen|funding|press|soil|FALSE|NG|TRUE|TRUE|FALSE|FALSE|NG|A|F|E|D|fortress|bullfights|opera|salt|shops|C|D|B|E|H|J|F|B|D|NG|NO|NO|YES|B|C|A|B|D',
 'cam17-test2': 'rock|cave|clay|Essenes|Hebrew|NG|FALSE|TRUE|TRUE|FALSE|FALSE|TRUE|NG|C|B|E|A|C|B|D|A|C|A|flavour~flavor|size|salt|D|A|A|C|A|NO|NG|YES|NO|NG|F|D|E|B',
 'cam17-test3': 'carnivorous|scent|pouch|fossil|habitat|TRUE|FALSE|NG|FALSE|NG|FALSE|TRUE|NG|F|G|A|H|B|E|C|B|C|solid|orangutan~orang-utan~Sumatran orangutan~Sumatran orang-utan|carbon stocks|biodiversity|D|B|C|D|C|NO|YES|NG|NO|H|D|I|B|F',
 'cam17-test4': 'FALSE|FALSE|NG|TRUE|NG|TRUE|droppings|coffee|mosquitoes|protein|unclean|culture|houses|E|A|D|F|C|descendants|sermon|fine|innovation|B|E|B|D|D|E|F|B|H|E|FALSE|NG|NG|TRUE|memory|numbers|communication|visual',
 'cam18-test1': 'lettuces|1,000 kg~1000 kg|consumption~food consumption|pesticides|journeys|producers|flavour~flavor|TRUE|NG|FALSE|TRUE|FALSE|NG|B|A|C|E|B|B|C|C|fire|nutrients|cavities|hawthorn|rare|C|F|A|E|B|sustainability|fuel|explosions|bankrupt|C|D|B|D|A',
 'cam18-test2': 'antlers~deer antlers|posts~timber posts|tree trunks|oxen|glaciers|druids|burial|calendar|TRUE|FALSE|FALSE|TRUE|NG|C|A|B|D|C|D|YES|NG|NO|YES|C|A|E|NG|NG|TRUE|FALSE|TRUE|NG|FALSE|transport|staircases|engineering|rule|Roman|Paris|outwards',
 'cam18-test3': 'G|D|C|F|architects|moisture|layers|speed|C|A|B|D|A|iii|viii|vi|v|vii|i|iv|A|C|B|speed|fifty~50|strict|B|A|C|C|H|D|F|E|B|NO|NG|YES|NO|NG',
 'cam18-test4': 'D|C|E|B|D|energy|food|gardening|obesity|C|D|A|D|B|C|D|C|B|A|E|B|D|YES|NO|NG|YES|YES|NG|NO|NO|I|F|A|C|H|E|B|A|D|C',
 'cam19-test1': 'FALSE|FALSE|NG|FALSE|NG|TRUE|TRUE|paint|topspin|training|intestines~gut|weights|grips|D|G|C|A|G|B|B|D|C|E|grain|punishment|ransom|D|A|C|D|G|J|H|B|E|C|YES|NG|NO|NG',
 'cam19-test2': 'piston|coal|workshops|labour~labor|quality|railway~railways|sanitation|NG|FALSE|NG|TRUE|TRUE|NG|D|F|A|C|F|injury|serves|excitement|Visualisation~Visualization|B|D|A|E|H|A|C|B|J|I|YES|NG|YES|NG|NO|C|B|D',
 'cam19-test3': 'FALSE|FALSE|TRUE|NG|TRUE|NG|FALSE|caves|stone|bones|beads|pottery|spices|G|A|H|B|carbon|fires|biodiversity|ditches|subsidence|A|C|D|B|D|A|C|B|C|E|F|B|NO|YES|NO|NG|NG|YES',
 'cam19-test4': 'FALSE|TRUE|FALSE|NG|FALSE|TRUE|colonies|spring|endangered|habitat~habitats|Europe|southern|diet|C|F|E|D|D|B|A|E|B|C|waste|machinery|caution|C|C|B|A|egalitarianism|status|hunting|domineering|autonomy|NG|NO|YES|NG|NO',
 'cam20-test1': 'FALSE|FALSE|FALSE|NG|TRUE|TRUE|bulbs|soil|feathers|deer|1980|funding|stakeholders|C|G|B|E|C|B|A|B|C|A|oak|flooring|keel|C|A|D|C|B|G|F|E|D|YES|NG|NO|YES|YES',
 'cam20-test2': 'tail|flippers|hair|seagrasses|lips|buoyancy|TRUE|NG|FALSE|NG|TRUE|NG|TRUE|B|F|B|laziness|anxious|threats|exams|perfectionists|guilt|A|C|A|E|NO|YES|NG|NG|NG|YES|F|D|H|B|G|B|D|C',
 'cam20-test3': 'potatoes|butter|meat|crystals|cellophane|tin|refrigerator|NG|TRUE|FALSE|TRUE|FALSE|NG|v|ii|iv|vii|iii|vi|C|E|B|D|tentacles|protection|colour~color|A|C|B|A|B|A|C|C|B|D|B|C|B|C',
 'cam20-test4': 'teacher|charcoal|skyscrapers|flowers|bones|landscape|rivers|FALSE|TRUE|FALSE|TRUE|NG|NG|C|A|D|F|pumps|dams|float|crops|trees|B|E|A|C|D|G|B|C|B|D|E|B|C|A|jackals|diseases|food|foxes',
}
MULTI = {
 'cam14-test1': [([4,5], ['traffic','crime']), ([19,20], ['B','D']), ([21,22], ['D','E'])],
 'cam14-test3': [([21,22], ['B','C'])],
 'cam14-test4': [([23,24], ['B','D']), ([25,26], ['B','E'])],
 'cam15-test1': [([23,24], ['C','D']), ([25,26], ['A','E'])],
 'cam17-test1': [([23,24], ['C','D']), ([25,26], ['B','E'])],
 'cam17-test3': [([21,22], ['B','C'])],
 'cam17-test4': [([23,24], ['B','E']), ([25,26], ['B','D'])],
 'cam18-test4': [([10,11], ['C','D']), ([12,13], ['A','D'])],
 'cam19-test1': [([20,21], ['B','D']), ([22,23], ['C','E'])],
 'cam19-test2': [([23,24], ['B','D']), ([25,26], ['A','E'])],
 'cam20-test2': [([23,24], ['A','C']), ([25,26], ['A','E'])],
 'cam20-test3': [([20,21], ['C','E']), ([22,23], ['B','D'])],
}
ERRATA = {
 'cam20-test3': [{
   'question': 19, 'sourcePrinted': 'vii', 'corrected': 'vi',
   'basis': 'Paragraph F promotes public hope; heading vi is Promoting hope. The supplied retyped key repeats vii from paragraph D.',
   'corroboration': [
      'https://onthiielts.com.vn/ielts-cambridge-20-test-3-reading-passage-2/',
      'https://langgo.edu.vn/cambridge-20-test-3-reading-passage-2-can-the-planets-coral-reefs-be-saved'],
 }, {
   'question': 26, 'sourcePrinted': 'colour', 'acceptedAdditionalVariant': 'color',
   'corroboration': ['https://onthiielts.com.vn/ielts-cambridge-20-test-3-reading-passage-2/'],
 }],
}


def source_for(book: int) -> Path:
    folder = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.endswith('Cambridge'))
    candidates = list((folder / f'CAMBRIDGE-{book}' / 'BAN_GOC').glob('*.pdf'))
    if book == 20:
        candidates = [p for p in candidates if p.name.startswith('Cam 20 -')]
    if len(candidates) != 1:
        raise ValueError(f'Ambiguous source for book {book}: {candidates}')
    return candidates[0]


def render_sources() -> None:
    import os
    import fitz
    # Tesseract C++ on Windows cannot read Unicode absolute tessdata paths.
    os.chdir(ROOT)
    out = ROOT / 'library/preparation/key-inspection'
    out.mkdir(parents=True, exist_ok=True)
    for book, pages in PAGES.items():
        with fitz.open(source_for(book)) as doc:
            for test, number in enumerate(pages, 1):
                page = doc[number - 1]
                prefix = out / f'cam{book}-test{test}'
                page.get_pixmap(matrix=fitz.Matrix(1.7,1.7)).save(str(prefix)+'.png')
                tp = page.get_textpage_ocr(language='eng', dpi=300, full=True,
                                          tessdata='library/preparation/tessdata')
                prefix.with_suffix('.txt').write_text(page.get_text(textpage=tp), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    if args.render:
        render_sources()
    out = ROOT / 'library/keys'
    out.mkdir(parents=True, exist_ok=True)
    report = []
    sources = {}
    assert set(DATA) == {f'cam{b}-test{t}' for b in PAGES for t in range(1,5)}
    for test_id, line in DATA.items():
        book, test = map(int, test_id.removeprefix('cam').split('-test'))
        values = line.split('|')
        assert len(values) == 40, (test_id, len(values))
        answers = {str(i): ['NOT GIVEN' if a == 'NG' else a for a in v.split('~')]
                   for i, v in enumerate(values, 1)}
        multi = [{'numbers': n, 'answers': a} for n, a in MULTI.get(test_id, [])]
        grouped = set()
        for group in multi:
            assert len(group['numbers']) == len(group['answers']) == len(set(group['answers']))
            for number in group['numbers']:
                assert 1 <= number <= 40 and number not in grouped
                assert answers[str(number)][0] in group['answers']
                grouped.add(number)
        if book not in sources:
            path = source_for(book)
            sources[book] = (path, hashlib.sha256(path.read_bytes()).hexdigest())
        path, digest = sources[book]
        provenance = {'source': path.relative_to(ROOT).as_posix(), 'sha256': digest,
                      'pdfPage': PAGES[book][test-1], 'verification': 'visual-source-key-review',
                      'scope': 'answer-key-only', 'questionContentVerified': False}
        result = {'id': test_id, 'version': '1', 'answers': answers,
                  'multi': multi, 'provenance': provenance}
        if test_id in ERRATA:
            result['errata'] = ERRATA[test_id]
        (out / f'{test_id}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
        report.append({'id': test_id, 'answerCount': len(answers), 'multiGroups': len(multi),
                       'errata': ERRATA.get(test_id, []), **provenance})
    report_path = ROOT / 'library/preparation/keys-report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({'keys': report, 'count': len(report),
        'note': 'Answer keys visually reviewed against supplied PDFs; this does not certify OCR passage/question text.'}, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(report)} private Reading keys ({len(report)*40} answers).')


if __name__ == '__main__':
    main()
