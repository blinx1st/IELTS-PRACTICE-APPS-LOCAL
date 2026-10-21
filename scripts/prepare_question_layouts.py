"""Source-reviewed, reproducible presentation metadata for Cambridge questions.

This changes layout only: the original group, source crops, answer keys and
reading content remain unchanged. presentation.json fingerprints the original
group so an old attempt can safely receive the same presentation at read time.
Run normally to apply; use --check for a non-mutating consistency audit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library"
VERSION = "layout1"


def cell(*content, header=False, row_span=1, col_span=1):
    result = {"content": list(content)}
    if header:
        result["header"] = True
    if row_span != 1:
        result["rowSpan"] = row_span
    if col_span != 1:
        result["colSpan"] = col_span
    return result


def blank(number, part=None):
    return {"number": number, **({"part": part} if part is not None else {})}


def table(*rows):
    return {"kind": "table", "rows": [{"cells": list(row)} for row in rows]}


# Each table was transcribed and visually compared to its original local crop,
# including the merged cells and all text surrounding every answer blank.
TABLES = {
    "cam13-t1-p1-g1": table(
        (cell("Section of website", header=True), cell("Comments", header=True)),
        (cell("Database of tourism services"), cell(
            "• easy for tourism-related businesses to get on the list\n\n"
            "• allowed businesses to ", blank(1), " information regularly\n\n"
            "• provided a country-wide evaluation of businesses, including their impact on the ", blank(2))),
        (cell("Special features on local topics"), cell(
            "• e.g. an interview with a former sports ", blank(3),
            ", and an interactive tour of various locations used in ", blank(4))),
        (cell("Information on driving routes"), cell("• varied depending on the ", blank(5))),
        (cell("Travel Planner"), cell(
            "• included a map showing selected places, details of public transport and local ", blank(6))),
        (cell("‘Your Words’"), cell("• travellers could send a link to their ", blank(7))),
    ),
    "cam13-t3-p1-g1": table(
        (cell("THE COCONUT PALM", header=True, col_span=3),),
        (cell("Part", header=True), cell("Description", header=True), cell("Uses", header=True)),
        (cell("trunk", header=True), cell("up to 30 metres"), cell("timber for houses and the making of ", blank(1))),
        (cell("leaves", header=True), cell("up to 6 metres long"), cell("to make brushes")),
        (cell("flowers", header=True), cell("at the top of the trunk"), cell(
            "stems provide sap, used as a drink or a source of ", blank(2))),
        (cell("fruits", header=True, row_span=5), cell("outer layer"), cell("")),
        (cell("middle layer (coir fibres)"), cell("used for ", blank(3), ", etc.")),
        (cell("inner layer (shell)"), cell("a source of ", blank(4), "\n\n(when halved) for ", blank(5))),
        (cell("coconut water"), cell("a drink\n\na source of ", blank(6), " for other plants")),
        (cell("coconut flesh"), cell("oil and milk for cooking and ", blank(7),
                                    "\n\nglycerine (an ingredient in ", blank(8), ")")),
    ),
    "cam15-t1-p1-g3": table(
        (cell("Middle Ages"), cell("Nutmeg was brought to Europe by the ", blank(8))),
        (cell("16th century"), cell("European nations took control of the nutmeg trade")),
        (cell("17th century"), cell(
            "Demand for nutmeg grew, as it was believed to be effective against the disease known as the ", blank(9),
            "\n\nThe Dutch\n"
            "– took control of the Banda Islands\n"
            "– restricted nutmeg production to a few areas\n"
            "– put ", blank(10), " on nutmeg to avoid it being cultivated outside the islands\n"
            "– finally obtained the island of ", blank(11), " from the British")),
        (cell("Late 18th century"), cell(
            "1770 – nutmeg plants were secretly taken to ", blank(12),
            "\n\n1778 – half the Banda Islands’ nutmeg plantations were destroyed by a ", blank(13))),
    ),
    "cam15-t4-p1-g2": table(
        (cell("Traditional uses of the huarango tree", header=True, col_span=2),),
        (cell("Part of tree", header=True), cell("Traditional use", header=True)),
        (cell(blank(6)), cell("fuel")),
        (cell(blank(7, 0), " and ", blank(7, 1)), cell("medicine")),
        (cell(blank(8)), cell("construction")),
    ),
    "cam17-t4-p1-g2": table(
        (cell("The study carried out by Rocha’s team", header=True, col_span=2),),
        (cell("Aim", header=True), cell(
            "• to investigate the feeding habits of bats in farmland near the Ranomafana National Park")),
        (cell("Method", header=True), cell(
            "• ultrasonic recording to identify favourite feeding spots\n\n• DNA analysis of bat ", blank(7))),
        (cell("Findings", header=True), cell(
            "• the bats\n\n"
            "  – were most active in rice fields located on hills\n\n"
            "  – ate pests of rice, ", blank(8), ", sugarcane, nuts and fruit\n\n"
            "  – prevent the spread of disease by eating ", blank(9), " and blackflies\n\n"
            "• local attitudes to bats are mixed:\n\n"
            "  – they provide food rich in ", blank(10), "\n\n"
            "  – the buildings where they roost become ", blank(11), "\n\n"
            "  – they play an important role in local ", blank(12))),
        (cell("Recommendation", header=True), cell(
            "• farmers should provide special ", blank(13), " to support the bat population")),
    ),
    "cam18-t1-p1-g2": table(
        (cell("Intensive farming versus aeroponic urban farming", header=True, col_span=4),),
        (cell("", header=True), cell("Growth", header=True), cell("Selection", header=True), cell("Sale", header=True)),
        (cell("Intensive farming", header=True),
         cell("• wide range of ", blank(4), " used\n\n• techniques pollute air"),
         cell("• quality not good\n\n• varieties of fruit and vegetables chosen that can survive long ", blank(5)),
         cell("• ", blank(6), " receive very little of overall income")),
        (cell("Aeroponic urban farming", header=True),
         cell("• no soil used\n\n• nutrients added to water, which is recycled"),
         cell("• produce chosen because of its ", blank(7)), cell("")),
    ),
}


def signature(group):
    original = {key: value for key, value in group.items() if key != "layout"}
    return hashlib.sha256(json.dumps(original, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def layout_for(group):
    if group.get('layout', {}).get('presentationVersion', 0) >= 3:
        return group['layout'] if group['layout']['kind'] == 'table' else None
    if group["id"] in TABLES:
        return TABLES[group["id"]]
    if group.get("layout", {}).get("kind") in ("table", "matrix"):
        return group["layout"]
    instructions = group.get("instructions", "").lower()
    kind = "headings" if "choose the correct heading" in instructions else (
        "paragraphs" if re.search(r"which (paragraph|section) contains", instructions) else None)
    if not kind:
        return None
    assert group["type"] == "matching", group["id"]
    rows = []
    for question in group["questions"]:
        text = question["text"].strip()
        if kind == "headings":
            # Retyped Cambridge 20 retains blank leaders in its old row text.
            text = re.sub(r"\s*[.\u2026]+\s*$", "", text)
            text = text[0].upper() + text[1:]
        rows.append({"number": question["number"], "text": text})
    return {"kind": "matrix", "matchingKind": kind, "rows": rows}


def validate(group, layout):
    numbers = [question["number"] for question in group["questions"]]
    if layout["kind"] == "matrix":
        assert [row["number"] for row in layout["rows"]] == numbers, group["id"]
        assert all(row["text"] for row in layout["rows"]), group["id"]
        options = group.get("options", [])
        assert options and len({option["value"] for option in options}) == len(options), group["id"]
        return numbers

    refs = []
    occupied = {}
    widths = []
    for row_number, row in enumerate(layout["rows"]):
        column = 0
        for item in row["cells"]:
            while (row_number, column) in occupied:
                column += 1
            rs, cs = item.get("rowSpan", 1), item.get("colSpan", 1)
            assert isinstance(rs, int) and isinstance(cs, int) and rs >= 1 and cs >= 1
            assert row_number + rs <= len(layout["rows"]), group["id"]
            for r in range(row_number, row_number + rs):
                for c in range(column, column + cs):
                    assert (r, c) not in occupied, (group["id"], r, c)
                    occupied[r, c] = True
            column += cs
            for token in item["content"]:
                if isinstance(token, str):
                    continue
                assert set(token) <= {"number", "part"}
                assert token["number"] in numbers, group["id"]
                if "part" in token:
                    assert group["id"] == "cam15-t4-p1-g2" and token["number"] == 7 and token["part"] in (0, 1)
                refs.append(token)
        widths.append(column)
    width = max(widths)
    assert all((r, c) in occupied for r in range(len(layout["rows"])) for c in range(width)), group["id"]
    assert {token["number"] for token in refs} == set(numbers), group["id"]
    expected = Counter({number: 2 if group["id"] == "cam15-t4-p1-g2" and number == 7 else 1 for number in numbers})
    assert Counter(token["number"] for token in refs) == expected, group["id"]
    return refs


def write_or_check(path, value, check):
    if check:
        assert path.exists(), f"Missing {path.relative_to(ROOT)}"
        assert json.loads(path.read_text(encoding="utf-8")) == value, f"Out of date: {path.relative_to(ROOT)}"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate generated layouts without changing files")
    args = parser.parse_args()
    presentation = json.loads((LIB / "presentation.json").read_text(encoding="utf-8")) if (LIB / "presentation.json").exists() else {"schemaVersion": 1, "groups": {}}
    reviewed = []
    counts = Counter()
    for path in sorted((LIB / "tests").glob("*.json")):
        test = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for passage in test["passages"]:
            for group in passage["groups"]:
                layout = layout_for(group)
                if layout is None:
                    continue
                refs = validate(group, layout)
                base_hash = signature(group)
                group["layout"] = layout
                changed = True
                presentation["groups"][group["id"]] = {**presentation["groups"].get(group["id"], {}), "baseSha256": base_hash, "layout": layout}
                category = layout.get("matchingKind", "table")
                counts[category] += 1
                reviewed.append({
                    "testId": test["id"], "groupId": group["id"], "kind": category,
                    "questionRefs": refs, "baseSha256": base_hash,
                    "layoutSha256": hashlib.sha256(json.dumps(layout, ensure_ascii=False, sort_keys=True,
                                                              separators=(",", ":")).encode("utf-8")).hexdigest(),
                    "sources": group.get("sourceImages", []),
                })
        if changed:
            if VERSION not in test["version"].split("."):
                test["version"] += "." + VERSION
            write_or_check(path, test, args.check)
            write_or_check(LIB / "preparation" / "overrides" / path.name, test, args.check)
    assert counts == {"table": 7, "headings": 7, "paragraphs": 31}, dict(counts)
    write_or_check(LIB / "presentation.json", presentation, args.check)
    report = {
        "schemaVersion": 1,
        "reviewDate": "2026-10-21",
        "method": "Seven table layouts and 38 matching matrices retained from source-reviewed metadata, including Cambridge 16. Original groups excluding layout are fingerprinted for safe presentation overlays on historic snapshots.",
        "counts": dict(counts),
        "totalGroups": len(reviewed),
        "errors": [],
        "checks": ["exact question coverage", "part indexes for the two blanks of one question", "rectangular merged-cell grid", "matrix row and option coverage", "source provenance", "original group fingerprints", "matching full overrides"],
        "groups": reviewed,
    }
    write_or_check(LIB / "preparation" / "question-layouts-review.json", report, args.check)
    print(json.dumps({"checked" if args.check else "prepared": len(reviewed), "counts": dict(counts), "errors": 0}))


if __name__ == "__main__":
    main()
