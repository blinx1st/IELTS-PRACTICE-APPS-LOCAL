"""Deterministic Academic Reading marking; no fuzzy spelling correction."""
import re
import unicodedata


def normalize(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or "")).strip()).casefold()


def within_limit(value, group):
    limit = group.get("wordLimit")
    if not limit:
        return True
    tokens = re.findall(r"\S+", str(value).strip())
    # IELTS counts a hyphenated expression as one word, numbers separately when allowed.
    words = [t for t in tokens if not re.fullmatch(r"[£$€]?\d[\d.,:/%-]*", t)]
    numbers = len(tokens) - len(words)
    if group.get("allowNumber"):
        return len(words) <= limit and numbers <= 1
    return len(tokens) <= limit


def band_for(score, skill='reading'):
    # Indicative Academic scale; thresholds vary slightly between official test versions.
    for minimum, band in [(39, 9), (37, 8.5), (35, 8), (32 if skill == 'listening' else 33, 7.5), (30, 7), (26 if skill == 'listening' else 27, 6.5),
                          (23, 6), (18 if skill == 'listening' else 19, 5.5), (16 if skill == 'listening' else 15, 5), (13, 4.5), (10, 4), (8, 3.5),
                          (6, 3), (4, 2.5), (3, 2), (2, 1.5), (1, 1), (0, 0)]:
        if score >= minimum:
            return band


def question_map(test):
    return {str(q["number"]): (p, g, q) for p in test.get('parts', test.get('passages', [])) for g in p["groups"] for q in g["questions"]}


def grade(test, key, answers, selected_numbers):
    lookup = question_map(test)
    rows = {}
    for n in selected_numbers:
        p, g, q = lookup[str(n)]
        value = str(answers.get(str(n), ""))
        accepted = key["answers"].get(str(n), [])
        limit_exceptions = {normalize(v) for v in key.get('limitExceptions', {}).get(str(n), [])}
        correct = bool(normalize(value)) and (within_limit(value, g) or normalize(value) in limit_exceptions) and normalize(value) in {normalize(v) for v in accepted}
        rows[str(n)] = {"number": n, "passage": p["number"], "type": g["type"], "answer": value,
                        "accepted": accepted, "status": "blank" if not normalize(value) else "correct" if correct else "incorrect"}
    for group in key.get("multi", []):
        nums = [str(n) for n in group["numbers"] if n in selected_numbers]
        if not nums:
            continue
        expected = list(dict.fromkeys(normalize(a) for a in group["answers"]))
        used = set()
        for n in nums:
            val = normalize(answers.get(n, ""))
            correct = bool(val) and val in expected and val not in used
            if val:
                used.add(val)
            rows[n].update(status="blank" if not val else "correct" if correct else "incorrect",
                           accepted=group["answers"], groupNumbers=group["numbers"])
    values = list(rows.values())
    score = sum(r["status"] == "correct" for r in values)
    breakdown = {}
    passages = {}
    for row in values:
        b = breakdown.setdefault(row["type"], {"correct": 0, "total": 0})
        b["total"] += 1
        b["correct"] += row["status"] == "correct"
        p = passages.setdefault(str(row["passage"]), {"correct": 0, "total": 0, "blank": 0})
        p["correct"] += row["status"] == "correct"
        p["total"] += 1
        p["blank"] += row["status"] == "blank"
    return {"score": score, "total": len(values), "band": band_for(score, test.get('skill', 'reading')) if len(values) == 40 else None,
            "blank": sum(r["status"] == "blank" for r in values),
            "rows": sorted(values, key=lambda r: r["number"]), "byType": breakdown, "byPassage": passages}
