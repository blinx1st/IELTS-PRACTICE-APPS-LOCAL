"""Record the completed visual reading review without changing question fields.

This is an editorial finalisation step, not an automatic OCR verification.
The source-page comparisons described in the reports were performed manually.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library"
PREP = LIB / "preparation"

SUBTITLES = {
    18: {(1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (3, 1), (3, 2)},
    19: {(1, 2), (1, 3), (3, 3), (4, 2), (4, 3)},
}
NOTES = {
    15: [
        "All twelve normalised passages were read and compared with all twenty-four source reading pages.",
        "Gray scan instructions were recovered using a binarised OCR pass. Paragraph labels, line endings and page continuations were checked against the scan.",
        "Final question and two minor reading punctuation corrections are recorded separately in cam15-questions-review.json and scripts/review_cam15_questions.py.",
    ],
    18: [
        "All twelve normalised passages were read and compared with all twenty-four source reading pages.",
        "Rotated source pages were rendered in their displayed orientation. Paragraph A-H labels, page continuations, footnotes and introductory subtitles were checked.",
        "Test 3 Passage 3 was reconstructed in left-column then right-column order from word coordinates. OCR fragments within the hiking analogy were repaired against pages 72-73.",
        "First-person I omitted by OCR in Test 4 Passage 3 was restored against the original. Château du Clos Lucé retains the source diacritics.",
        "The awkward printed wording 'all home to constructed tall, wooden buildings' in Test 3 Passage 1 was retained as supplied.",
    ],
    19: [
        "All twelve normalised passages were read and compared with all twenty-four source reading pages.",
        "Promotional embedded text on scanned pages was excluded from the reading body and did not bypass OCR.",
        "Test 2 Passage 3 was reconstructed in left-column then right-column order. Paragraph labels, page continuations, footnotes and subtitles were checked.",
        "WWFN and 1990 in Test 3 Passage 2, and 130 butterfly species in Test 4 Passage 1, are retained as printed in the supplied source.",
        "The !Kung name and the first-person 'I believe' in Test 4 Passage 3 were restored against the scan.",
    ],
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def main():
    provenance = json.loads((PREP / "sources.json").read_text(encoding="utf-8"))
    for book in [15, 18, 19]:
        rows = []
        for test in range(1, 5):
            file = LIB / "tests" / f"cam{book}-test{test}.json"
            item = json.loads(file.read_text(encoding="utf-8"))
            question_before = digest([p["groups"] for p in item["passages"]])
            if book in [18, 19]:
                for passage in item["passages"]:
                    for paragraph in passage["paragraphs"]:
                        if paragraph["text"].startswith("*"):
                            paragraph["kind"] = "footnote"
                        if book == 18 and test == 2 and passage["number"] == 3:
                            paragraph["text"] = paragraph["text"].replace("Chateau du Clos Lucé", "Château du Clos Lucé")
                    if (test, passage["number"]) in SUBTITLES[book]:
                        passage["paragraphs"][0]["kind"] = "subtitle"
                    if book == 18 and test == 4 and passage["number"] == 3:
                        passage["paragraphs"][0]["kind"] = "byline"
                        passage["paragraphs"][1]["kind"] = "subheading"
                item["version"] = "2026-10-21.5"
                item["verification"] = {
                    "status": "verified",
                    "note": "All 12 reading passages and 160 question slots in this book were compared with the supplied PDFs. Source-image task layouts and native options, numbering and word limits were checked separately.",
                    "readingReport": f"library/preparation/cam{book}-reading-review.json",
                    "questionsReport": "library/preparation/cam18-19-questions-review.json",
                    "keysReport": "library/preparation/keys-report.json",
                }
                assert question_before == digest([p["groups"] for p in item["passages"]]), "Question fields changed during reading finalisation"
                file.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                (PREP / "overrides" / file.name).write_text(file.read_text(encoding="utf-8"), encoding="utf-8")
            passages = []
            for passage in item["passages"]:
                passages.append({
                    "number": passage["number"],
                    "title": passage["title"],
                    "sourceFile": passage["sourcePages"][0]["file"],
                    "physicalReadingPages": [ref["page"] for ref in passage.get("sourceImages", [])],
                    "sourceImages": passage.get("sourceImages", []),
                    "reviewContact": f"library/preparation/reading-review/cam{book}-t{test}-p{passage['number']}.jpg",
                    "paragraphLabels": [p["label"] for p in passage["paragraphs"] if p.get("label")],
                    "readingSha256": digest({"title": passage["title"], "paragraphs": passage["paragraphs"]}),
                })
            rows.append({"id": item["id"], "version": item["version"], "jsonSha256": hashlib.sha256(file.read_bytes()).hexdigest(), "passages": passages})
        report = {
            "book": book,
            "scope": "Reading titles, subtitles, paragraphs, labels, footnotes and page/column order; question content is reviewed in a separate report.",
            "status": "visually_reviewed",
            "passagesReviewed": 12,
            "sourceReadingPagesReviewed": sum(len(p["physicalReadingPages"]) for row in rows for p in row["passages"]),
            "method": "Manual comparison of the complete normalised text with locally rendered source pages. Contact sheets retain the full original page edges; no generated replacement prose was used.",
            "sourcePdf": [x for x in provenance["sources"] if f"CAMBRIDGE-{book}" in x["file"]],
            "notes": NOTES[book],
            "tests": rows,
        }
        (PREP / f"cam{book}-reading-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Cambridge {book}: {report['passagesReviewed']} passages / {report['sourceReadingPagesReviewed']} reading pages; question fields unchanged")


if __name__ == "__main__":
    main()
