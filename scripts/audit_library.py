"""Audit local Cambridge JSON/assets without claiming an OCR editorial review.

Run from any directory: python scripts/audit_library.py
Writes a reproducible structural report. Exit 1 means a blocking structural issue.
Visual sample findings are recorded explicitly below, with a narrow review scope.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.scoring import grade, normalize, within_limit

BOOKS = (13, 14, 15, 16, 17, 18, 19, 20)
KINDS = {"completion", "short", "matching", "choice", "multi", "tfng", "ynng"}
ROMANS = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit_library():
    issues = []
    records = []
    source_exceptions = []
    image_count = 0
    group_count = 0

    def issue(severity, code, test, detail, **location):
        issues.append(dict(severity=severity, code=code, test=test, detail=detail, **location))

    expected = {f"cam{b}-test{t}" for b in BOOKS for t in range(1, 5)}
    actual = {p.stem for p in (ROOT / "library/tests").glob("*.json")}
    for missing in sorted(expected - actual):
        issue("error", "missing_test", missing, "Expected Cambridge test JSON is absent.")

    for test_id in sorted(expected & actual):
        path = ROOT / "library/tests" / f"{test_id}.json"
        test = load(path)
        key_path = ROOT / "library/keys" / path.name
        if not key_path.exists():
            issue("error", "missing_key", test_id, "Private answer key JSON is absent.")
            continue
        key = load(key_path)
        if test.get("id") != test_id or key.get("id") != test_id:
            issue("error", "id_mismatch", test_id, "Test/key IDs must match their filename.")
        passages = test.get("passages", [])
        if [p.get("number") for p in passages] != [1, 2, 3]:
            issue("error", "passage_numbers", test_id, "Expected exactly ordered passages 1, 2, 3.")
        numbers = [q.get("number") for p in passages for g in p.get("groups", []) for q in g.get("questions", [])]
        counts = Counter(numbers)
        if sorted(numbers) != list(range(1, 41)):
            issue("error", "question_numbers", test_id, "Must contain each question number 1–40 exactly once.",
                  missing=sorted(set(range(1, 41))-set(numbers)), duplicates=[n for n, c in counts.items() if c > 1])
        if set(key.get("answers", {})) != {str(n) for n in range(1, 41)}:
            issue("error", "answer_numbers", test_id, "Answer key must cover exactly questions 1–40.")

        empty_questions = []
        source_groups = []
        canonical = {}
        for passage in passages:
            pno = passage.get("number")
            if not passage.get("title", "").strip() or passage.get("title", "").startswith("Reading Passage "):
                issue("error", "missing_title", test_id, "Passage needs its original title.", passage=pno)
            text = " ".join(p.get("text", "") for p in passage.get("paragraphs", []))
            if not text.strip():
                issue("error", "missing_passage_text", test_id, "Passage has no extracted text.", passage=pno)
            elif len(text.split()) < 450:
                issue("warning", "short_passage", test_id, "Passage is unusually short; compare against its PDF.", passage=pno, words=len(text.split()))
            labels = [p["label"] for p in passage.get("paragraphs", []) if p.get("label")]
            if labels:
                valid_labels = all(re.fullmatch(r"[A-Z]", label) for label in labels)
                expected_labels = [chr(n) for n in range(ord("A"), ord(max(labels))+1)] if valid_labels else []
                if labels != expected_labels:
                    issue("warning", "paragraph_label_sequence", test_id,
                          "Extracted paragraph labels have gaps/duplicates; verify source labels or use faithful reading images.",
                          passage=pno, labels=labels)

            images = list(passage.get("sourceImages", []))
            for page in passage.get("sourcePages", []):
                if not (ROOT / page.get("file", "")).is_file():
                    issue("error", "missing_source_pdf", test_id, "Source PDF path is missing.", passage=pno, source=page)
            for group in passage.get("groups", []):
                group_count += 1
                gid = group.get("id")
                kind = group.get("type")
                questions = group.get("questions", [])
                nums = [q["number"] for q in questions]
                loc = dict(passage=pno, group=gid, numbers=nums)
                if kind not in KINDS:
                    issue("error", "unknown_type", test_id, f"Unknown question type {kind!r}.", **loc)
                if not nums or nums != list(range(min(nums), max(nums)+1)):
                    issue("error", "group_numbers", test_id, "Group questions must be a nonempty ordered contiguous range.", **loc)
                group_images = group.get("sourceImages", [])
                images.extend(group_images)
                if not group_images:
                    issue("error", "missing_group_images", test_id, "Question group has no original source image for checking OCR/layout.", **loc)
                if group.get("renderMode") == "source":
                    source_groups.append(gid)
                if not group.get("instructions", "").strip():
                    issue("error", "missing_instructions", test_id,
                          "Question group needs its original task directions independent of its body/source image.", **loc)
                directions = group.get("instructions", "") + "\n" + group.get("body", "")
                # Instructions are independent from the question prompt in the
                # interactive UI; the OCR continuation parser must not consume Q1.
                if re.search(r"(?m)^\s*\d{1,2}\s*$", group.get("instructions", "")):
                    issue("warning", "question_in_instructions", test_id,
                          "Directions contain a standalone question number; check for a swallowed first prompt.", **loc)
                range_match = re.search(r"\bA\s*[-–—]\s*([B-Z])\b", group.get("instructions", ""))
                if kind in {"matching", "multi"} and range_match:
                    needed = {chr(i) for i in range(ord("A"), ord(range_match[1])+1)}
                    present = {str(o.get("value", "")) for o in group.get("options", [])}
                    # A-F in a heading task names paragraphs, while its controls
                    # legitimately contain i-viii. Check those labels separately.
                    is_heading_task = bool(present) and present.issubset(set(ROMANS))
                    if not is_heading_task and needed-present:
                        missing = sorted(needed-present)
                        if test_id == "cam15-test4" and gid == "cam15-t4-p3-g1" and missing == ["J"]:
                            source_exceptions.append(dict(test=test_id, group=gid, code="printed_range_typo",
                                detail="The supplied PDF page 92 says A–J but prints only A–I. The Cambridge 15 question reviewer visually confirmed nine original options; retain source wording without inventing option J."))
                        else:
                            issue("error", "instruction_option_range", test_id,
                                  "Original directions specify options that are absent from the control.",
                                  missing=missing, **loc)
                    paragraph_range = re.search(r"(?:paragraphs|sections)[^\n.]*\bA\s*[-–—]\s*([B-Z])\b", group.get("instructions", ""), re.I)
                    if paragraph_range and not needed.issubset(set(labels)):
                        issue("error", "required_paragraph_labels", test_id,
                              "Paragraph/section matching requires labels missing from the interactive reading text.",
                              missing=sorted(needed-set(labels)), **loc)
                roman_range = re.search(r"\bi\s*[-–—]\s*(ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)\b", group.get("instructions", ""))
                if kind == "matching" and roman_range:
                    needed = set(ROMANS[:ROMANS.index(roman_range[1])+1])
                    present = {str(o.get("value", "")) for o in group.get("options", [])}
                    if needed-present:
                        issue("error", "instruction_roman_range", test_id,
                              "Original directions specify Roman headings absent from the control.", missing=sorted(needed-present), **loc)
                key_values = [normalize(v) for n in nums for v in key.get("answers", {}).get(str(n), [])]
                if any(v in {"true", "false"} for v in key_values) and kind != "tfng":
                    issue("error", "type_key_mismatch", test_id, "TRUE/FALSE key requires tfng controls.", **loc)
                if any(v in {"yes", "no"} for v in key_values) and kind != "ynng":
                    issue("error", "type_key_mismatch", test_id, "YES/NO key requires ynng controls.", **loc)
                if kind in {"tfng", "ynng"}:
                    allowed = {"true", "false", "not given"} if kind == "tfng" else {"yes", "no", "not given"}
                    if any(v not in allowed for v in key_values):
                        issue("error", "boolean_key_mismatch", test_id, "Boolean control cannot submit an accepted answer.", **loc)
                if kind in {"completion", "short"} and not group.get("wordLimit"):
                    issue("warning", "missing_word_limit", test_id, "Completion/short group has no word-limit metadata.", **loc)
                if kind == "multi":
                    matching_multi = [m for m in key.get("multi", []) if m.get("numbers") == nums]
                    if len(matching_multi) != 1 or group.get("choose") != len(nums):
                        issue("error", "multi_key_group", test_id, "Multi-select range/choose must match one private unordered marking group.", **loc)

                for q in questions:
                    n = q["number"]
                    answers = key.get("answers", {}).get(str(n), [])
                    if not answers or not all(isinstance(v, str) and v.strip() for v in answers):
                        issue("error", "empty_answer", test_id, "Question has no accepted answer.", question=n, **loc)
                        continue
                    canonical[str(n)] = answers[0]
                    if not within_limit(answers[0], group):
                        issue("error", "canonical_word_limit", test_id, "Canonical answer is rejected by this group's word limit.", question=n, answer=answers[0], **loc)
                    for answer in answers[1:]:
                        if not within_limit(answer, group):
                            issue("warning", "variant_word_limit", test_id, "Listed alternative is over the group's word limit and cannot be accepted.", question=n, answer=answer, **loc)
                    if not q.get("text", "").strip() and kind not in {"completion", "short", "multi"}:
                        empty_questions.append(n)
                    if kind in {"choice", "matching", "multi"}:
                        opts = q.get("options", group.get("options", []))
                        values = [str(o.get("value", "")) for o in opts]
                        normalized = {normalize(v) for v in values}
                        if not values:
                            issue("error", "empty_select_options", test_id, "Select group has no options.", question=n, **loc)
                        if len(values) != len(set(values)) or any(not v.strip() for v in values):
                            issue("error", "duplicate_select_options", test_id, "Select options contain blank or repeated values.", question=n, **loc)
                        for answer in answers:
                            if normalize(answer) not in normalized:
                                issue("error", "unselectable_answer", test_id, "Accepted answer is not among the selectable values.", question=n, answer=answer, values=values, **loc)
                        if values and all(v in ROMANS for v in values):
                            last = max(ROMANS.index(v) for v in values)
                            if values != list(ROMANS[:last+1]):
                                issue("error", "roman_option_gap", test_id, "Roman matching list has a missing or reordered heading.", question=n, values=values, **loc)
                        elif values and any(re.fullmatch(r"[A-Z]", v) for v in values):
                            letters = [v for v in values if re.fullmatch(r"[A-Z]", v)]
                            full = [chr(i) for i in range(ord("A"), ord(max(letters))+1)]
                            if set(values) != set(full):
                                issue("error", "letter_option_gap", test_id, "Letter list has a missing value or mixed Roman OCR token.", question=n, values=values, **loc)
                        if any(not o.get("label", "").strip() for o in opts):
                            issue("error", "empty_option_label", test_id, "Select option label is blank.", question=n, **loc)
                        if any(re.search(r"\b(?:answer sheet|in boxes|any letter more than once)\b", o.get("label", ""), re.I) for o in opts):
                            issue("error", "instruction_as_option_label", test_id,
                                  "An option label contains directions, suggesting an OCR option-list boundary error.", question=n, **loc)

            for source in images:
                image_count += 1
                url = source.get("url", "")
                if not re.fullmatch(r"/library-assets/[^/\\]+\.(webp|png|jpg)", url):
                    issue("error", "asset_url", test_id, "Source asset URL is not a local library-assets filename.", passage=pno, source=source)
                elif not (ROOT / "library/assets" / url.removeprefix("/library-assets/")).is_file():
                    issue("error", "missing_source_image", test_id, "Referenced source image is absent.", passage=pno, source=source)
                if not isinstance(source.get("page"), int) or source["page"] < 1:
                    issue("error", "source_page", test_id, "Source image needs a positive PDF page number.", passage=pno, source=source)

        for multi in key.get("multi", []):
            nums = multi.get("numbers", [])
            if len(nums) != len(set(nums)) or not set(nums).issubset(set(numbers)) or len(multi.get("answers", [])) != len(nums):
                issue("error", "invalid_private_multi", test_id, "Private unordered group must have distinct existing numbers and one distinct answer per mark.", multi=multi)
            if len({normalize(v) for v in multi.get("answers", [])}) != len(nums):
                issue("error", "repeated_multi_answer", test_id, "Private unordered group repeats an answer, so full marks are impossible.", multi=multi)
        if set(canonical) == {str(n) for n in range(1, 41)} and sorted(numbers) == list(range(1, 41)):
            result = grade(test, key, canonical, list(range(1, 41)))
            if result["score"] != 40:
                issue("error", "canonical_score", test_id, "Submitting all canonical keys does not score 40/40.", score=result["score"], rejected=[r["number"] for r in result["rows"] if r["status"] != "correct"])
            reversed_multi = dict(canonical)
            for multi in key.get("multi", []):
                for n, value in zip(multi["numbers"], reversed(multi["answers"])):
                    reversed_multi[str(n)] = value
            if grade(test, key, reversed_multi, list(range(1, 41)))["score"] != 40:
                issue("error", "unordered_score", test_id, "Reversing unordered group answers loses marks.")

        records.append(dict(id=test_id, passages=len(passages), questions=len(numbers),
                            groups=sum(len(p.get("groups", [])) for p in passages),
                            verification=test.get("verification"), sourceRenderedGroups=source_groups,
                            emptyExtractedQuestionTexts=empty_questions,
                            testSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            keySha256=hashlib.sha256(key_path.read_bytes()).hexdigest()))

    # Each question can share a group-level issue. Keep one record per distinct
    # group failure unless the specific question/accepted value matters.
    return dict(schemaVersion=1, generatedAt=datetime.now(timezone.utc).isoformat(),
                scope="All expected local Cambridge test JSON, private keys, referenced files, scoring compatibility; not a complete passage transcription review.",
                summary=dict(expectedTests=32, actualTests=len(records), passages=sum(r["passages"] for r in records),
                             questions=sum(r["questions"] for r in records), groups=group_count,
                             sourceImageReferences=image_count,
                             errors=sum(i["severity"] == "error" for i in issues),
                             warnings=sum(i["severity"] == "warning" for i in issues)),
                tests=records, issues=issues, sourceExceptions=source_exceptions,
                visualReview={"status": "See source-specific visual samples recorded during the implementation audit.", "samples": []},
                limitations=[
                    "File existence and URL-shape checks do not prove crop contents or complete PDF transcription.",
                    "OCR spelling, missing in-line paragraph labels, and merged question prompts require visual editorial review.",
                    "A canonical score of 40 verifies data/control compatibility, not that the answer key matches the printed book.",
                    "Empty extracted question text may be usable through a source-rendered original layout; it is recorded rather than treated as verified text.",
                    "This audit never upgrades content verification status."
                ])


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "library/preparation/content-audit.json")
    args = parser.parse_args()
    report = audit_library()
    # Preserve narrow, manually recorded visual samples on repeated audit runs.
    if args.output.exists():
        old = load(args.output)
        if old.get("visualReview", {}).get("samples"):
            report["visualReview"] = old["visualReview"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
