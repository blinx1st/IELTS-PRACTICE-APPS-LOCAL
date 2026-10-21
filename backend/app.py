from __future__ import annotations

from contextlib import contextmanager

import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
import uuid
import zipfile
from urllib.parse import urlparse
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.scoring import grade, question_map
from backend.presentation import present, part_counts
from backend.listening import units, initial_player, control, stale, duration
from backend import backups

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "library"
DATA = Path(os.environ.get("READING_ROOM_DATA", ROOT / "data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "reading-room.sqlite3"
LOCK = threading.RLock()
app = FastAPI(title="Reading Room Local", docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])


@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, updated REAL NOT NULL, payload TEXT NOT NULL)")
    try:
        with db:
            yield db
    finally:
        db.close()


with connect() as _db:
    pass


@app.middleware("http")
async def local_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
        if urlparse(origin).hostname not in ("127.0.0.1", "localhost", "testserver"):
            return JSONResponse({"detail": "Yêu cầu phải xuất phát từ ứng dụng local."}, status_code=403)
    result = await call_next(request)
    if request.url.path.startswith("/api"):
        result.headers["Cache-Control"] = "no-store"
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_test(test_id):
    if not test_id.startswith("cam") or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in test_id):
        raise HTTPException(404, "Không tìm thấy đề.")
    base = LIBRARY / 'listening' if '-listening-' in test_id else LIBRARY
    file = base / "tests" / f"{test_id}.json"
    if not file.exists():
        raise HTTPException(404, "Đề chưa được chuẩn bị.")
    test = read_json(file)
    key_file = base / "keys" / f"{test_id}.json"
    key = read_json(key_file) if key_file.exists() else {"answers": {}, "multi": []}
    return test, key


def ready(test, key):
    numbers = sorted(int(n) for n in question_map(test))
    if test.get('skill') == 'listening':
        return (test.get('verification', {}).get('status') == 'verified'
                and [u['number'] for u in units(test)] == [1, 2, 3, 4]
                and all(len([q for g in u['groups'] for q in g['questions']]) == 10
                        and u.get('audio', {}).get('verification', {}).get('status') == 'verified'
                        and (LIBRARY / 'audio' / Path(u['audio']['url']).name).is_file() for u in units(test))
                and numbers == list(range(1, 41))
                and all(key.get('answers', {}).get(str(n)) for n in numbers))
    return (test.get("verification", {}).get("status") == "verified"
            and len(test["passages"]) == 3
            and sum(len(g["questions"]) for p in test["passages"] for g in p["groups"]) == 40
            and numbers == list(range(1, 41))
            and all(key.get("answers", {}).get(str(n)) for n in numbers))


def save(db, a):
    a["updatedAt"] = time.time()
    db.execute("INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET updated=excluded.updated,payload=excluded.payload",
               (a["id"], a["updatedAt"], json.dumps(a, ensure_ascii=False)))


def expire(db, a):
    if stale(a): save(db, a)
    if a["status"] == "active" and a.get("deadline") is not None and time.time() >= a["deadline"]:
        a.update(status="submitted", submittedAt=a["deadline"], revision=a["revision"] + 1, autoSubmitted=True)
        save(db, a)
    return a


def get_attempt(db, attempt_id):
    row = db.execute("SELECT payload FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Không tìm thấy lượt làm bài.")
    return expire(db, json.loads(row[0]))


def public(a, include_test=True):
    result = {k: v for k, v in a.items() if k not in ("keySnapshot", "testSnapshot", "transcriptSnapshot")}
    if include_test:
        result["test"] = present(a["testSnapshot"], LIBRARY)
    result.setdefault('answerParts', {})
    result.setdefault('skill', 'reading')
    if a['mode'] == 'exam':
        result.setdefault('examTiming', 'timed')
    result["serverNow"] = time.time()
    return result


@app.get("/api/health")
def health():
    return {"app": "reading-room-local", "version": "2.0.0", "workspace": hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]}


@app.post("/api/shutdown")
async def shutdown(request: Request):
    token = request.headers.get("x-reading-room-token", "")
    if not token or token != os.environ.get("READING_ROOM_SHUTDOWN_TOKEN"):
        raise HTTPException(403, "Chỉ công cụ dừng app trên máy được thực hiện thao tác này.")
    import signal
    def stop():
        time.sleep(.3)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=stop, daemon=True).start()
    return {"stopping": True}


@app.get("/api/library")
def library(skill: Literal['reading', 'listening'] = 'reading'):
    books = []
    for book in range(13, 21):
        tests = []
        for n in range(1, 5):
            tid = f"cam{book}-{'listening-' if skill == 'listening' else ''}test{n}"
            try:
                t, k = load_test(tid)
                tests.append({"id": tid, "book": book, "test": n, "title": t["title"], "ready": ready(t, k),
                              "verification": t.get("verification", {}),
                              "skill": skill, "passages": [{"number": p["number"], "title": p["title"], "questions": len([q for g in p["groups"] for q in g["questions"]])} for p in units(t)]})
            except HTTPException:
                tests.append({"id": tid, "skill": skill, "book": book, "test": n, "title": f"Cambridge {book} · Test {n}", "ready": False, "passages": []})
        books.append({"number": book, "available": any(t['ready'] for t in tests), "tests": tests})
    return {"books": books, 'skill': skill, "readyCount": sum(t["ready"] for b in books for t in b["tests"])}


class Start(BaseModel):
    testId: str
    mode: str = "exam"
    passage: int | None = None
    minutes: int = Field(default=20, ge=0, le=180)
    examTiming: Literal['timed', 'untimed'] = 'timed'
    skill: Literal['reading', 'listening'] = 'reading'
    part: int | None = Field(default=None, ge=1, le=4)


@app.post("/api/attempts")
def start(body: Start):
    t, k = load_test(body.testId)
    if t.get('skill', 'reading') != body.skill:
        raise HTTPException(422, 'Kỹ năng không khớp với đề đã chọn.')
    if not ready(t, k):
        raise HTTPException(409, "Đề đang được đối chiếu nội dung và đáp án, chưa sẵn sàng để làm bài.")
    if body.mode not in ("exam", "practice"):
        raise HTTPException(422, "Chế độ không hợp lệ.")
    listening = body.skill == 'listening'
    if not listening and body.mode == "practice" and body.passage not in [p["number"] for p in t["passages"]]:
        raise HTTPException(422, "Hãy chọn passage.")
    selected_part = body.part if listening else body.passage
    numbers = sorted(int(n) for n, (p, _, _) in question_map(t).items() if body.mode == "exam" or (listening and selected_part is None) or p["number"] == selected_part)
    now = time.time()
    seconds = (3600 if body.examTiming == 'timed' else 0) if body.mode == "exam" else body.minutes * 60
    if listening: seconds = 0
    version = hashlib.sha256(json.dumps([t, k], sort_keys=True).encode()).hexdigest()[:16]
    a = {"id": str(uuid.uuid4()), "testId": t["id"], "title": t["title"], "book": t["book"],
         "testNumber": t["test"], "contentVersion": version, "testSnapshot": t, "keySnapshot": k,
         "mode": body.mode, "passage": body.passage if body.mode == "practice" else None,
         "numbers": numbers, "startedAt": now, "deadline": now + seconds if seconds else None,
         "duration": seconds or None, "remaining": seconds or None, "status": "active", "revision": 0,
         "answers": {}, "answerParts": {}, "flags": [], "annotations": [], "currentPassage": body.passage or 1, "result": None}
    a['skill'] = body.skill
    if listening:
        tp = LIBRARY / 'listening' / 'transcripts' / (body.testId + '.json')
        if not tp.is_file(): raise HTTPException(409, 'Transcript chưa được kiểm tra.')
        a.update(part=body.part if body.mode == 'practice' else None, passage=None,
                 currentPassage=body.part or 1, player=initial_player(t, body.part if body.mode == 'practice' else None),
                 transcriptSnapshot=read_json(tp), duration=duration(t) if body.mode == 'exam' else None,
                 examTiming='timed' if body.mode == 'exam' else 'untimed')
    elif body.mode == 'exam':
        a['examTiming'] = body.examTiming
        if body.examTiming == 'untimed':
            a.update(elapsedSeconds=0, elapsedStartedAt=now)
    with LOCK, connect() as db:
        save(db, a)
    return public(a)


@app.get("/api/attempts")
def attempts(skill: Literal['reading', 'listening'] | None = None):
    with LOCK, connect() as db:
        data = [expire(db, json.loads(r[0])) for r in db.execute("SELECT payload FROM attempts ORDER BY updated DESC").fetchall()]
    return [public(a, False) for a in data if skill is None or a.get('skill', 'reading') == skill]


@app.get("/api/attempts/{attempt_id}")
def attempt(attempt_id: str):
    with LOCK, connect() as db:
        return public(get_attempt(db, attempt_id))


class Draft(BaseModel):
    revision: int
    answers: dict[str, str] = Field(default_factory=dict)
    flags: list[int] = Field(default_factory=list, max_length=40)
    annotations: list[dict] = Field(default_factory=list, max_length=1000)
    currentPassage: int = 1
    answerParts: dict[str, list[str]] | None = None


@app.patch("/api/attempts/{attempt_id}")
def update(attempt_id: str, body: Draft):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a["status"] not in ("active", "paused"):
            raise HTTPException(409, "Bài đã nộp. Đáp án được giữ nguyên.")
        if a["revision"] != body.revision:
            raise HTTPException(409, "Bài đã thay đổi ở tab khác. Hãy mở lại lượt làm bài.")
        nums = set(map(str, a["numbers"]))
        if any(n not in nums or len(v) > 1000 for n, v in body.answers.items()):
            raise HTTPException(422, "Đáp án không hợp lệ.")
        answers = dict(body.answers)
        parts = dict(a.get('answerParts', {})) if body.answerParts is None else dict(body.answerParts)
        counts = part_counts(present(a['testSnapshot'], LIBRARY))
        if any(n not in nums or n not in counts or len(v) != counts[n] or any(len(x) > 1000 for x in v) for n, v in parts.items()):
            raise HTTPException(422, 'Các ô trả lời trong bảng không hợp lệ.')
        if body.answerParts is None:
            parts = {n: v for n, v in parts.items() if answers.get(n, '') == a['answers'].get(n, '')}
        for n, values in parts.items():
            answers[n] = ' '.join(values).strip()
            if len(answers[n]) > 1000:
                raise HTTPException(422, 'Đáp án trong bảng quá dài.')
        if len(json.dumps(body.annotations)) > 2_000_000:
            raise HTTPException(422, "Ghi chú quá lớn.")
        if a["status"] == "paused" and (answers != a["answers"] or parts != a.get('answerParts', {}) or body.annotations != a["annotations"]):
            raise HTTPException(409, "Tiếp tục bài trước khi thay đổi đáp án.")
        a.update(answers=answers, answerParts=parts, flags=sorted(set(n for n in body.flags if str(n) in nums)),
                 annotations=body.annotations, currentPassage=body.currentPassage, revision=a["revision"] + 1)
        save(db, a)
        return public(a)


@app.post("/api/attempts/{attempt_id}/pause")
def pause(attempt_id: str):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a.get('skill') == 'listening': raise HTTPException(409, 'Use the Listening audio controls.')
        if a["status"] != "active" or not (a['mode'] == 'practice' or a.get('examTiming') == 'untimed'):
            raise HTTPException(409, "Chỉ có thể tạm dừng luyện tập hoặc thi thử không hạn giờ.")
        if a.get('examTiming') == 'untimed':
            a['elapsedSeconds'] += max(0, time.time() - a['elapsedStartedAt'])
            a['elapsedStartedAt'] = None
        a.update(remaining=max(0, a["deadline"] - time.time()) if a["deadline"] else None,
                 deadline=None, status="paused", revision=a["revision"] + 1)
        save(db, a)
        return public(a)


@app.post("/api/attempts/{attempt_id}/resume")
def resume(attempt_id: str):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a.get('skill') == 'listening': raise HTTPException(409, 'Use the Listening audio controls.')
        if a["status"] != "paused":
            raise HTTPException(409, "Bài không ở trạng thái tạm dừng.")
        if a.get('examTiming') == 'untimed':
            a['elapsedStartedAt'] = time.time()
        a.update(deadline=time.time() + a["remaining"] if a["remaining"] is not None else None,
                 status="active", revision=a["revision"] + 1)
        save(db, a)
        return public(a)


@app.post('/api/attempts/{attempt_id}/untimed')
def make_untimed(attempt_id: str):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a.get('skill') == 'listening': raise HTTPException(409, 'Use Switch to practice in the Listening player.')
        if a['mode'] != 'exam' or a['status'] != 'active':
            raise HTTPException(409, 'Chỉ chuyển được bài thi thử còn đang làm, chưa hết giờ.')
        if a.get('examTiming') != 'untimed':
            now = time.time()
            a.update(examTiming='untimed', elapsedSeconds=max(0, now - a['startedAt']), elapsedStartedAt=now,
                     deadline=None, duration=None, remaining=None, revision=a['revision'] + 1)
            save(db, a)
        return public(a)


@app.post("/api/attempts/{attempt_id}/submit")
def submit(attempt_id: str):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a["status"] in ("active", "paused"):
            if a.get('player'): a['player'].update(running=False, phase='finished', leaseOwner=None, leaseUntil=0)
            if a.get('examTiming') == 'untimed' and a.get('elapsedStartedAt') is not None:
                a['elapsedSeconds'] += max(0, time.time() - a['elapsedStartedAt'])
                a['elapsedStartedAt'] = None
            a.update(status="submitted", submittedAt=time.time(), revision=a["revision"] + 1)
            save(db, a)
        return public(a)


@app.post("/api/attempts/{attempt_id}/grade")
def mark(attempt_id: str):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a["status"] not in ("submitted", "graded"):
            raise HTTPException(409, "Hãy nộp bài trước khi chấm.")
        if a["status"] == "submitted":
            result = grade(a["testSnapshot"], a["keySnapshot"], a["answers"], a["numbers"])
            a.update(status="graded", gradedAt=time.time(), result=result, revision=a["revision"] + 1)
            save(db, a)
        return public(a)


@app.get("/api/statistics")
def statistics(skill: Literal['reading', 'listening'] | None = None):
    rows = [a for a in attempts(skill) if a["status"] == "graded"]
    groups = {}
    for a in rows:
        for typ, value in a["result"]["byType"].items():
            g = groups.setdefault(typ, {"correct": 0, "total": 0})
            g["correct"] += value["correct"]
            g["total"] += value["total"]
    return {"attempts": len(rows), "correct": sum(a["result"]["score"] for a in rows),
            "total": sum(a["result"]["total"] for a in rows), "byType": groups}


class PlayerCommand(BaseModel):
    action: Literal['claim', 'play', 'pause', 'checkpoint', 'seek', 'next', 'interrupt', 'practice', 'release']
    clientId: str = Field(min_length=8, max_length=100)
    part: int | None = Field(default=None, ge=1, le=4)
    position: float | None = None
    rate: float | None = None
    loopA: float | None = None
    loopB: float | None = None
    clearLoop: bool = False


@app.post('/api/attempts/{attempt_id}/player')
def player(attempt_id: str, body: PlayerCommand):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        control(a, body)
        save(db, a)
        return public(a)


@app.get('/api/attempts/{attempt_id}/transcript')
def transcript(attempt_id: str):
    with LOCK, connect() as db:
        a = get_attempt(db, attempt_id)
        if a.get('skill') != 'listening' or a['status'] != 'graded':
            raise HTTPException(409, 'Chỉ mở transcript sau khi chấm bài.')
        return a['transcriptSnapshot']


@app.get('/library-audio/{name}')
def audio_asset(name: str):
    root = (LIBRARY / 'audio').resolve()
    target = (root / name).resolve()
    if not target.is_relative_to(root) or not target.is_file() or target.suffix.lower() not in ('.mp3', '.m4a', '.wav', '.ogg'):
        raise HTTPException(404, 'Không tìm thấy audio.')
    return FileResponse(target, media_type='audio/mp4' if target.suffix == '.m4a' else 'audio/mpeg')


@app.get('/api/backup')
def backup():
    with LOCK, connect() as db:
        rows = [json.loads(r[0]) for r in db.execute('SELECT payload FROM attempts').fetchall()]
    return backups.export(rows, LIBRARY)


@app.post('/api/restore')
async def restore(file: UploadFile = File(...)):
    return await backups.import_archive(file, LIBRARY, connect, LOCK)


(LIBRARY / "assets").mkdir(parents=True, exist_ok=True)
app.mount("/library-assets", StaticFiles(directory=LIBRARY / "assets"), name="library-assets")


@app.get("/{path:path}")
def frontend(path: str):
    dist = ROOT / "dist"
    candidate = (dist / path).resolve()
    if candidate.is_relative_to(dist.resolve()) and candidate.is_file():
        return FileResponse(candidate)
    if path.startswith("api/"):
        raise HTTPException(404, "Không tìm thấy API.")
    if (dist / "index.html").exists():
        return FileResponse(dist / "index.html")
    return JSONResponse({"detail": "Chưa có giao diện. Chạy cài đặt lần đầu để build app."}, status_code=503)
