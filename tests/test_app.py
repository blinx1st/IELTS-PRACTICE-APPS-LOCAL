import copy
import io
import json
from pathlib import Path
import zipfile

import pytest
from fastapi.testclient import TestClient
import backend.app as server
from backend.scoring import band_for, grade, normalize, within_limit


@pytest.fixture
def fixture_data(tmp_path, monkeypatch):
    groups = [
        {"id": "g1", "type": "completion", "instructions": "ONE WORD", "body": "", "wordLimit": 1, "questions": [{"number": 1, "text": ""}]},
        {"id": "g2", "type": "tfng", "instructions": "", "body": "", "questions": [{"number": 2, "text": "Statement"}]},
        {"id": "g3", "type": "ynng", "instructions": "", "body": "", "questions": [{"number": 3, "text": "Claim"}]},
        {"id": "g4", "type": "matching", "instructions": "", "body": "", "options": [{"value": "iv", "label": "Heading"}], "questions": [{"number": 4, "text": ""}]},
        {"id": "g5", "type": "choice", "instructions": "", "body": "", "questions": [{"number": 5, "text": "Choose", "options": [{"value": "B", "label": "Correct"}]}]},
        {"id": "g6", "type": "multi", "instructions": "", "body": "", "choose": 2, "questions": [{"number": 6, "text": ""}, {"number": 7, "text": ""}], "options": [{"value": "A", "label": "One"}, {"value": "C", "label": "Two"}]},
        {"id": "g7", "type": "completion", "wordLimit": 1, "allowNumber": True, "instructions": "", "body": "", "questions": [{"number": 8, "text": ""}]},
        {"id": "g8", "type": "short", "instructions": "", "body": "", "questions": [{"number": n, "text": ""} for n in range(9, 14)]},
    ]
    test = {"id": "cam20-test1", "book": 20, "test": 1, "title": "Test fixture", "version": "1", "verification": {"status": "verified"},
            "passages": [{"id": "p1", "number": 1, "title": "One", "paragraphs": [{"id": "p1-a", "text": "Text"}], "groups": groups}]}
    for n, numbers in [(2, range(14, 27)), (3, range(27, 41))]:
        test["passages"].append({"id": f"p{n}", "number": n, "title": str(n), "paragraphs": [{"id": f"p{n}-a", "text": "Text"}], "groups": [{"id": f"rest{n}", "type": "completion", "instructions": "", "body": "", "questions": [{"number": i, "text": ""} for i in numbers]}]})
    key = {"answers": {str(n): ["answer"] for n in range(1, 41)}, "multi": [{"numbers": [6, 7], "answers": ["A", "C"]}]}
    key["answers"].update({"1": ["bulbs"], "2": ["NOT GIVEN"], "3": ["NO"], "4": ["iv"], "5": ["B"], "6": ["A"], "7": ["C"], "8": ["May 2020"]})
    lib = tmp_path / "library"
    (lib / "tests").mkdir(parents=True)
    (lib / "keys").mkdir()
    (lib / "tests/cam20-test1.json").write_text(json.dumps(test), encoding="utf-8")
    (lib / "keys/cam20-test1.json").write_text(json.dumps(key), encoding="utf-8")
    monkeypatch.setattr(server, "DB", tmp_path / "history.sqlite3")
    monkeypatch.setattr(server, "LIBRARY", lib)
    return test, key, TestClient(server.app)


def start(client, **extra):
    response = client.post("/api/attempts", json={"testId": "cam20-test1", **extra})
    assert response.status_code == 200, response.text
    return response.json()


def draft(client, a, **extra):
    return client.patch("/api/attempts/" + a["id"], json={"revision": a["revision"], "answers": a["answers"], "flags": a["flags"], "annotations": a["annotations"], "currentPassage": 1, **extra})


def test_correct_all_and_question_types(fixture_data):
    t, k, _ = fixture_data
    answers = {n: values[0] for n, values in k["answers"].items()}
    answers["6"], answers["7"] = "C", "A"
    result = grade(t, k, answers, list(range(1, 41)))
    assert result["score"] == 40 and result["band"] == 9
    assert len(result["byType"]) == 7
    assert result["byPassage"] == {"1": {"correct": 13, "total": 13, "blank": 0}, "2": {"correct": 13, "total": 13, "blank": 0}, "3": {"correct": 14, "total": 14, "blank": 0}}


def test_normalization_and_limits(fixture_data):
    t, k, _ = fixture_data
    assert normalize("  BuLBS  ") == "bulbs"
    assert normalize("NOT    GIVEN") == "not given"
    assert within_limit("forest-dwelling", {"wordLimit": 1})
    assert within_limit("May 2020", {"wordLimit": 1, "allowNumber": True})
    assert not within_limit("May June 2020", {"wordLimit": 1, "allowNumber": True})
    r = grade(t, k, {"1": "bulbs extra", "2": "not given", "3": "not"}, [1, 2, 3, 4])
    assert r["score"] == 1 and r["blank"] == 1


def test_multi_partial_and_duplicate(fixture_data):
    t, k, _ = fixture_data
    assert grade(t, k, {"6": "C", "7": "A"}, [6, 7])["score"] == 2
    assert grade(t, k, {"6": "A", "7": "A"}, [6, 7])["score"] == 1
    assert grade(t, k, {"6": "C", "7": "D"}, [6, 7])["score"] == 1


@pytest.mark.parametrize("score,band", [(0, 0), (15, 5), (23, 6), (30, 7), (35, 8), (37, 8.5), (39, 9), (40, 9)])
def test_band_thresholds(score, band):
    assert band_for(score) == band


def test_draft_persists_and_no_key_exposure(fixture_data):
    _, _, c = fixture_data
    a = start(c)
    assert a["deadline"] == a["startedAt"] + 3600
    assert "keySnapshot" not in a and "testSnapshot" not in a and a["result"] is None
    updated = draft(c, a, answers={"1": "bulbs"}, flags=[1], annotations=[{"id": "n", "anchor": "p1-a", "text": "Text", "start": 0, "end": 4, "note": "Nhớ"}]).json()
    reopened = c.get("/api/attempts/" + a["id"]).json()
    assert reopened["answers"] == {"1": "bulbs"} and reopened["flags"] == [1]
    assert reopened["annotations"][0]["note"] == "Nhớ"
    assert reopened["deadline"] == a["deadline"] and reopened["revision"] == updated["revision"]


def test_review_before_grade_and_immutable_snapshot(fixture_data):
    _, key, c = fixture_data
    a = start(c)
    assert c.post(f"/api/attempts/{a['id']}/grade").status_code == 409
    a = draft(c, a, answers={"1": "bulbs"}).json()
    submitted = c.post(f"/api/attempts/{a['id']}/submit").json()
    assert submitted["status"] == "submitted" and submitted["result"] is None
    assert draft(c, submitted, answers={"1": "wrong"}).status_code == 409
    # Updating the library cannot change an existing attempt's answer-key snapshot.
    key["answers"]["1"] = ["different"]
    (server.LIBRARY / "keys/cam20-test1.json").write_text(json.dumps(key), encoding="utf-8")
    marked = c.post(f"/api/attempts/{a['id']}/grade").json()
    assert marked["result"]["score"] == 1 and marked["result"]["rows"][0]["accepted"] == ["bulbs"]
    assert c.post(f"/api/attempts/{a['id']}/grade").json()["result"] == marked["result"]


def test_conflict_does_not_overwrite(fixture_data):
    _, _, c = fixture_data
    a = start(c)
    assert draft(c, a, answers={"1": "bulbs"}).status_code == 200
    assert draft(c, a, answers={"1": "wrong"}).status_code == 409
    assert c.get(f"/api/attempts/{a['id']}").json()["answers"]["1"] == "bulbs"


def test_exam_expiry_and_reopen(fixture_data, monkeypatch):
    _, _, c = fixture_data
    a = start(c)
    draft(c, a, answers={"1": "bulbs"})
    monkeypatch.setattr(server.time, "time", lambda: a["deadline"] + 10)
    expired = c.get(f"/api/attempts/{a['id']}").json()
    assert expired["status"] == "submitted" and expired["autoSubmitted"]
    assert expired["answers"]["1"] == "bulbs" and expired["result"] is None
    assert draft(c, expired, answers={"1": "wrong"}).status_code == 409


def test_practice_pause_resume_and_no_band(fixture_data):
    _, _, c = fixture_data
    a = start(c, mode="practice", passage=1, minutes=20)
    assert a["numbers"] == list(range(1, 14)) and a["duration"] == 1200
    paused = c.post(f"/api/attempts/{a['id']}/pause").json()
    assert paused["status"] == "paused" and paused["deadline"] is None
    assert draft(c, paused, answers={"1": "bulbs"}).status_code == 409
    resumed = c.post(f"/api/attempts/{a['id']}/resume").json()
    assert resumed["status"] == "active" and resumed["deadline"] > resumed["serverNow"]
    c.post(f"/api/attempts/{a['id']}/submit")
    result = c.post(f"/api/attempts/{a['id']}/grade").json()["result"]
    assert result["total"] == 13 and result["band"] is None
    untimed = start(c, mode="practice", passage=2, minutes=0)
    assert untimed["deadline"] is None
    exam = start(c)
    assert c.post(f"/api/attempts/{exam['id']}/pause").status_code == 409


def test_invalid_and_unverified(fixture_data):
    t, _, c = fixture_data
    assert c.post("/api/attempts", json={"testId": t["id"], "mode": "practice", "passage": 4}).status_code == 422
    assert c.post("/api/attempts", json={"testId": t["id"], "minutes": -1}).status_code == 422
    a = start(c)
    assert draft(c, a, answers={"41": "x"}).status_code == 422
    t["verification"]["status"] = "needs_review"
    (server.LIBRARY / "tests/cam20-test1.json").write_text(json.dumps(t), encoding="utf-8")
    assert c.post("/api/attempts", json={"testId": t["id"]}).status_code == 409
    assert c.post("/api/attempts", json={"testId": "../secrets"}).status_code == 404


def test_backup_restore_merge_and_corruption(fixture_data, monkeypatch, tmp_path):
    _, _, c = fixture_data
    a = start(c)
    draft(c, a, answers={"1": "bulbs"})
    raw = c.get("/api/backup").content
    monkeypatch.setattr(server, "DB", tmp_path / "restored.sqlite3")
    assert c.post("/api/restore", files={"file": ("backup.zip", raw, "application/zip")}).json() == {"restored": 1}
    assert c.get(f"/api/attempts/{a['id']}").json()["answers"] == {"1": "bulbs"}
    assert c.post("/api/restore", files={"file": ("backup.zip", raw, "application/zip")}).json() == {"restored": 0}
    assert c.post("/api/restore", files={"file": ("bad.zip", b"not zip", "application/zip")}).status_code == 422


def test_backup_includes_source_images_and_rejects_traversal(fixture_data, monkeypatch, tmp_path):
    t, _, c = fixture_data
    assets = server.LIBRARY / "assets"
    assets.mkdir()
    (assets / "source.webp").write_bytes(b"fixture-image-bytes")
    t["passages"][0]["sourceImages"] = [{"url": "/library-assets/source.webp", "page": 1}]
    (server.LIBRARY / "tests/cam20-test1.json").write_text(json.dumps(t), encoding="utf-8")
    a = start(c)
    raw = c.get("/api/backup").content
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.read("assets/source.webp") == b"fixture-image-bytes"
        manifest = json.loads(z.read("reading-room-backup.json"))
    new_lib = tmp_path / "restored-library"
    monkeypatch.setattr(server, "DB", tmp_path / "image-restored.sqlite3")
    monkeypatch.setattr(server, "LIBRARY", new_lib)
    assert c.post("/api/restore", files={"file": ("backup.zip", raw, "application/zip")}).json()["restored"] == 1
    assert (new_lib / "assets/source.webp").read_bytes() == b"fixture-image-bytes"
    assert c.get(f"/api/attempts/{a['id']}").json()["test"]["passages"][0]["sourceImages"]
    manifest["assets"] = {"../escape": "bad"}
    bad = io.BytesIO()
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("reading-room-backup.json", json.dumps(manifest))
    assert c.post("/api/restore", files={"file": ("bad.zip", bad.getvalue(), "application/zip")}).status_code == 422


def test_full_workflow_without_external_network(fixture_data, monkeypatch):
    import socket
    _, _, c = fixture_data
    original = socket.socket.connect
    def local_only(sock, address):
        if isinstance(address, tuple) and address[0] not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError("App attempted external network access")
        return original(sock, address)
    monkeypatch.setattr(socket.socket, "connect", local_only)
    assert c.get("/api/library").status_code == 200
    a = start(c)
    a = draft(c, a, answers={"1": "bulbs"}).json()
    assert c.post(f"/api/attempts/{a['id']}/submit").json()["result"] is None
    assert c.post(f"/api/attempts/{a['id']}/grade").json()["result"]["score"] == 1
    assert c.get("/api/statistics").json()["correct"] == 1
    assert c.get("/api/backup").status_code == 200


def test_cross_origin_is_rejected(fixture_data):
    _, _, c = fixture_data
    assert c.post("/api/attempts", json={"testId": "cam20-test1"}, headers={"Origin": "https://example.com"}).status_code == 403
    assert c.get("/api/health").json()["app"] == "reading-room-local"


def test_real_library_keys_mark_as_expected():
    root = Path(__file__).resolve().parents[1] / "library"
    if not (root / "tests").exists():
        pytest.skip("Library preparation is still running")
    problems = []
    for path in sorted((root / "tests").glob("*.json")):
        test = json.loads(path.read_text(encoding="utf-8"))
        key_path = root / "keys" / path.name
        if not key_path.exists():
            problems.append(f"{path.stem}: missing keys")
            continue
        key = json.loads(key_path.read_text(encoding="utf-8"))
        answers = {n: values[0] for n, values in key["answers"].items()}
        for group in key.get("multi", []):
            for n, value in zip(group["numbers"], group["answers"]):
                answers[str(n)] = value
        try:
            result = grade(test, key, answers, list(range(1, 41)))
            if result["score"] != 40:
                problems.append(f"{path.stem}: canonical key failed at {[r['number'] for r in result['rows'] if r['status'] != 'correct']}")
        except (KeyError, TypeError) as e:
            problems.append(f"{path.stem}: {e}")
    assert not problems, "\n".join(problems)


def test_untimed_exam_elapsed_pause_resume_and_reopen(fixture_data, monkeypatch):
    _, _, c = fixture_data
    a = start(c, examTiming='untimed')
    assert a['numbers'] == list(range(1, 41)) and a['deadline'] is None and a['duration'] is None
    assert a['elapsedSeconds'] == 0 and a['elapsedStartedAt'] == a['startedAt']
    a = draft(c, a, answers={'1': 'bulbs'}, flags=[1]).json()
    monkeypatch.setattr(server.time, 'time', lambda: a['startedAt'] + 90)
    paused = c.post(f"/api/attempts/{a['id']}/pause").json()
    assert paused['elapsedSeconds'] == 90 and paused['elapsedStartedAt'] is None
    monkeypatch.setattr(server.time, 'time', lambda: a['startedAt'] + 500)
    reopened = c.get(f"/api/attempts/{a['id']}").json()
    assert reopened['status'] == 'paused' and reopened['elapsedSeconds'] == 90
    assert draft(c, reopened, answers={'1': 'wrong'}).status_code == 409
    resumed = c.post(f"/api/attempts/{a['id']}/resume").json()
    assert resumed['elapsedSeconds'] == 90 and resumed['elapsedStartedAt'] == a['startedAt'] + 500
    monkeypatch.setattr(server.time, 'time', lambda: a['startedAt'] + 36000)
    active = c.get(f"/api/attempts/{a['id']}").json()
    assert active['status'] == 'active' and active['deadline'] is None
    submitted = c.post(f"/api/attempts/{a['id']}/submit").json()
    assert submitted['elapsedSeconds'] == 35590 and submitted['elapsedStartedAt'] is None
    result = c.post(f"/api/attempts/{a['id']}/grade").json()['result']
    assert result['score'] == 1 and result['total'] == 40 and result['band'] is not None


def test_switch_untimed_preserves_work_and_is_idempotent(fixture_data, monkeypatch):
    _, _, c = fixture_data
    a = start(c)
    a = draft(c, a, answers={'1': 'bulbs'}, flags=[1], annotations=[{'id': 'h', 'anchor': 'p1-a', 'start': 0, 'end': 4, 'text': 'Text', 'note': ''}]).json()
    monkeypatch.setattr(server.time, 'time', lambda: a['startedAt'] + 123)
    switched = c.post(f"/api/attempts/{a['id']}/untimed").json()
    assert switched['examTiming'] == 'untimed' and switched['elapsedSeconds'] == 123
    assert switched['deadline'] is None and switched['duration'] is None
    for field in ['answers', 'annotations', 'flags', 'contentVersion', 'test']:
        assert switched[field] == a[field]
    assert c.post(f"/api/attempts/{a['id']}/untimed").json()['revision'] == switched['revision']
    assert c.post(f"/api/attempts/{a['id']}/pause").status_code == 200
    practice = start(c, mode='practice', passage=1)
    assert c.post(f"/api/attempts/{practice['id']}/untimed").status_code == 409


def test_cannot_switch_expired_or_submitted_exam(fixture_data, monkeypatch):
    _, _, c = fixture_data
    a = start(c)
    monkeypatch.setattr(server.time, 'time', lambda: a['deadline'] + 1)
    assert c.post(f"/api/attempts/{a['id']}/untimed").status_code == 409
    expired = c.get(f"/api/attempts/{a['id']}").json()
    assert expired['status'] == 'submitted' and expired['autoSubmitted']
    b = start(c)
    c.post(f"/api/attempts/{b['id']}/submit")
    assert c.post(f"/api/attempts/{b['id']}/untimed").status_code == 409
    assert c.post('/api/attempts', json={'testId': b['testId'], 'examTiming': 'invalid'}).status_code == 422


def test_table_parts_save_partial_grade_as_one_and_backup(fixture_data, monkeypatch, tmp_path):
    t, k, c = fixture_data
    t['passages'][0]['groups'][0].update(wordLimit=2, layout={'kind': 'table', 'rows': [{'cells': [{'content': [{'number': 1, 'part': 0}, ' and ', {'number': 1, 'part': 1}]}]}]})
    k['answers']['1'] = ['leaves bark', 'bark leaves']
    (server.LIBRARY/'tests/cam20-test1.json').write_text(json.dumps(t), encoding='utf-8')
    (server.LIBRARY/'keys/cam20-test1.json').write_text(json.dumps(k), encoding='utf-8')
    a = start(c)
    a = draft(c, a, answerParts={'1': ['', 'bark']}).json()
    assert a['answerParts']['1'] == ['', 'bark'] and a['answers']['1'] == 'bark'
    a = draft(c, a, answerParts={'1': ['leaves', 'bark']}).json()
    assert a['answers']['1'] == 'leaves bark'
    assert draft(c, a, answerParts={'1': ['leaves']}).status_code == 422
    assert draft(c, a, answerParts={'2': ['x', 'y']}).status_code == 422
    c.post(f"/api/attempts/{a['id']}/submit")
    result = c.post(f"/api/attempts/{a['id']}/grade").json()['result']
    assert result['score'] == 1 and result['total'] == 40
    raw = c.get('/api/backup').content
    monkeypatch.setattr(server, 'DB', tmp_path/'parts-restored.sqlite3')
    assert c.post('/api/restore', files={'file': ('backup.zip', raw)}).json()['restored'] == 1
    restored = c.get(f"/api/attempts/{a['id']}").json()
    assert restored['answerParts']['1'] == ['leaves', 'bark'] and restored['result'] == result


def test_presentation_overlay_does_not_mutate_historical_snapshot(fixture_data):
    import hashlib
    from backend.presentation import signature
    t, _, c = fixture_data
    a = start(c)
    group = t['passages'][0]['groups'][0]
    layout = {'kind': 'table', 'rows': [{'cells': [{'content': [{'number': 1}]}]}]}
    (server.LIBRARY/'presentation.json').write_text(json.dumps({'groups': {group['id']: {'baseSha256': signature(group), 'layout': layout}}}), encoding='utf-8')
    with server.connect() as db:
        before = json.loads(db.execute('SELECT payload FROM attempts WHERE id=?', (a['id'],)).fetchone()[0])
    presented = c.get(f"/api/attempts/{a['id']}").json()
    assert presented['test']['passages'][0]['groups'][0]['layout'] == layout
    with server.connect() as db:
        after = json.loads(db.execute('SELECT payload FROM attempts WHERE id=?', (a['id'],)).fetchone()[0])
    assert before == after and 'layout' not in after['testSnapshot']['passages'][0]['groups'][0]
    assert presented['contentVersion'] == a['contentVersion'] and 'keySnapshot' not in presented
    group['body'] = 'Changed source'
    (server.LIBRARY/'presentation.json').write_text(json.dumps({'groups': {group['id']: {'baseSha256': signature(group), 'layout': layout}}}), encoding='utf-8')
    assert 'layout' not in c.get(f"/api/attempts/{a['id']}").json()['test']['passages'][0]['groups'][0]


def test_backup_restores_paused_countup_and_new_annotations(fixture_data, monkeypatch, tmp_path):
    _, _, c = fixture_data
    a = start(c, examTiming='untimed')
    annotations = [
        {'id': 'h', 'kind': 'highlight', 'level': 3, 'anchor': 'p1-a', 'start': 0, 'end': 4, 'text': 'Text'},
        {'id': 'n', 'kind': 'note', 'note': 'Independent', 'anchor': 'p1-a', 'start': 0, 'end': 4, 'text': 'Text'},
    ]
    a = draft(c, a, answers={'1': 'bulbs'}, annotations=annotations).json()
    monkeypatch.setattr(server.time, 'time', lambda: a['startedAt'] + 45)
    assert c.post(f"/api/attempts/{a['id']}/pause").json()['elapsedSeconds'] == 45
    raw = c.get('/api/backup').content
    monkeypatch.setattr(server, 'DB', tmp_path/'paused-countup.sqlite3')
    monkeypatch.setattr(server.time, 'time', lambda: a['startedAt'] + 3600)
    assert c.post('/api/restore', files={'file': ('backup.zip', raw)}).json()['restored'] == 1
    restored = c.get(f"/api/attempts/{a['id']}").json()
    assert restored['elapsedSeconds'] == 45 and restored['elapsedStartedAt'] is None
    assert restored['status'] == 'paused' and restored['annotations'] == annotations
    resumed = c.post(f"/api/attempts/{a['id']}/resume").json()
    assert resumed['elapsedSeconds'] == 45 and resumed['elapsedStartedAt'] == a['startedAt'] + 3600
