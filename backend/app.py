from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "library"
DATA = Path(os.environ.get("READING_ROOM_DATA", ROOT / "data"))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / "reading-room.sqlite3"
LOCK = threading.RLock()
app = FastAPI(title="Reading Room Local", docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])


def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, updated REAL NOT NULL, payload TEXT NOT NULL)")
    return db


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
    file = LIBRARY / "tests" / f"{test_id}.json"
    if not file.exists():
        raise HTTPException(404, "Đề chưa được chuẩn bị.")
    test = read_json(file)
    key_file = LIBRARY / "keys" / f"{test_id}.json"
    key = read_json(key_file) if key_file.exists() else {"answers": {}, "multi": []}
    return test, key


def ready(test, key):
    numbers = sorted(int(n) for n in question_map(test))
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
    result = {k: v for k, v in a.items() if k not in ("keySnapshot", "testSnapshot")}
    if include_test:
        result["test"] = present(a["testSnapshot"], LIBRARY)
    result.setdefault('answerParts', {})
    if a['mode'] == 'exam':
        result.setdefault('examTiming', 'timed')
    result["serverNow"] = time.time()
    return result


@app.get("/api/health")
def health():
    return {"app": "reading-room-local", "version": "1.1.0", "workspace": hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]}


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
def library():
    books = []
    for book in range(13, 21):
        tests = []
        for n in range(1, 5):
            tid = f"cam{book}-test{n}"
            try:
                t, k = load_test(tid)
                tests.append({"id": tid, "book": book, "test": n, "title": t["title"], "ready": ready(t, k),
                              "verification": t.get("verification", {}),
                              "passages": [{"number": p["number"], "title": p["title"], "questions": len([q for g in p["groups"] for q in g["questions"]])} for p in t["passages"]]})
            except HTTPException:
                tests.append({"id": tid, "book": book, "test": n, "title": f"Cambridge {book} · Test {n}", "ready": False, "passages": []})
        books.append({"number": book, "available": book != 16, "tests": tests})
    return {"books": books, "readyCount": sum(t["ready"] for b in books for t in b["tests"])}


class Start(BaseModel):
    testId: str
    mode: str = "exam"
    passage: int | None = None
    minutes: int = Field(default=20, ge=0, le=180)
    examTiming: Literal['timed', 'untimed'] = 'timed'


@app.post("/api/attempts")
def start(body: Start):
    t, k = load_test(body.testId)
    if not ready(t, k):
        raise HTTPException(409, "Đề đang được đối chiếu nội dung và đáp án, chưa sẵn sàng để làm bài.")
    if body.mode not in ("exam", "practice"):
        raise HTTPException(422, "Chế độ không hợp lệ.")
    if body.mode == "practice" and body.passage not in [p["number"] for p in t["passages"]]:
        raise HTTPException(422, "Hãy chọn passage.")
    numbers = sorted(int(n) for n, (p, _, _) in question_map(t).items() if body.mode == "exam" or p["number"] == body.passage)
    now = time.time()
    seconds = (3600 if body.examTiming == 'timed' else 0) if body.mode == "exam" else body.minutes * 60
    version = hashlib.sha256(json.dumps([t, k], sort_keys=True).encode()).hexdigest()[:16]
    a = {"id": str(uuid.uuid4()), "testId": t["id"], "title": t["title"], "book": t["book"],
         "testNumber": t["test"], "contentVersion": version, "testSnapshot": t, "keySnapshot": k,
         "mode": body.mode, "passage": body.passage if body.mode == "practice" else None,
         "numbers": numbers, "startedAt": now, "deadline": now + seconds if seconds else None,
         "duration": seconds or None, "remaining": seconds or None, "status": "active", "revision": 0,
         "answers": {}, "answerParts": {}, "flags": [], "annotations": [], "currentPassage": body.passage or 1, "result": None}
    if body.mode == 'exam':
        a['examTiming'] = body.examTiming
        if body.examTiming == 'untimed':
            a.update(elapsedSeconds=0, elapsedStartedAt=now)
    with LOCK, connect() as db:
        save(db, a)
    return public(a)


@app.get("/api/attempts")
def attempts():
    with LOCK, connect() as db:
        data = [expire(db, json.loads(r[0])) for r in db.execute("SELECT payload FROM attempts ORDER BY updated DESC").fetchall()]
    return [public(a, False) for a in data]


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
def statistics():
    rows = [a for a in attempts() if a["status"] == "graded"]
    groups = {}
    for a in rows:
        for typ, value in a["result"]["byType"].items():
            g = groups.setdefault(typ, {"correct": 0, "total": 0})
            g["correct"] += value["correct"]
            g["total"] += value["total"]
    return {"attempts": len(rows), "correct": sum(a["result"]["score"] for a in rows),
            "total": sum(a["result"]["total"] for a in rows), "byType": groups}


@app.get("/api/backup")
def backup():
    with LOCK, connect() as db:
        rows = [json.loads(r[0]) for r in db.execute("SELECT payload FROM attempts").fetchall()]
    stream = io.BytesIO()
    assets = {}
    def collect(value):
        if isinstance(value, dict):
            for v in value.values():
                collect(v)
        elif isinstance(value, list):
            for v in value:
                collect(v)
        elif isinstance(value, str) and value.startswith("/library-assets/"):
            name = value.removeprefix("/library-assets/")
            path = (LIBRARY / "assets" / name).resolve()
            if path.is_relative_to((LIBRARY / "assets").resolve()) and path.is_file():
                assets[name] = path
    for a in rows:
        collect(a["testSnapshot"])
    asset_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in assets.items()}
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("reading-room-backup.json", json.dumps({"format": "reading-room", "version": 1, "createdAt": time.time(), "attempts": rows, "assets": asset_hashes}, ensure_ascii=False))
        for name, path in assets.items():
            z.write(path, "assets/" + name)
    return Response(stream.getvalue(), media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="reading-room-backup.zip"'})


@app.post("/api/restore")
async def restore(file: UploadFile = File(...)):
    raw = await file.read(256_000_001)
    if len(raw) > 256_000_000:
        raise HTTPException(413, "Bản sao lưu vượt quá 256 MB.")
    restored_assets = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            info = z.getinfo("reading-room-backup.json")
            if info.file_size > 100_000_000:
                raise ValueError("Bản giải nén quá lớn")
            data = json.loads(z.read(info))
            if sum(i.file_size for i in z.infolist()) > 512_000_000:
                raise ValueError("Bản giải nén quá lớn")
            for name, expected in data.get("assets", {}).items():
                if not name or Path(name).name != name or "/" in name or "\\" in name:
                    raise ValueError("Đường dẫn tài liệu không hợp lệ")
                content = z.read("assets/" + name)
                if hashlib.sha256(content).hexdigest() != expected:
                    raise ValueError("Tài liệu bị hỏng")
                destination = LIBRARY / "assets" / name
                if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
                    raise ValueError("Tài liệu trùng tên khác nội dung")
                restored_assets[name] = content
        if data["format"] != "reading-room" or data["version"] != 1 or not isinstance(data["attempts"], list):
            raise ValueError("Định dạng không hợp lệ")
        for a in data["attempts"]:
            uuid.UUID(a["id"])
            assert a["status"] in ("active", "paused", "submitted", "graded")
            assert isinstance(a["updatedAt"], (float, int))
            assert isinstance(a["answers"], dict) and isinstance(a["numbers"], list)
            assert set(map(str, a["numbers"])) <= set(question_map(a["testSnapshot"]))
            assert all(str(n) in a["keySnapshot"]["answers"] for n in a["numbers"])
            assert a["status"] != "graded" or isinstance(a["result"]["rows"], list)
            for name in ("revision", "startedAt", "deadline", "duration", "remaining", "annotations", "flags", "testId", "title", "book", "mode", "currentPassage"):
                a[name]
    except Exception:
        raise HTTPException(422, "Tệp sao lưu không hợp lệ hoặc bị hỏng.")
    restored = 0
    with LOCK, connect() as db:
        (LIBRARY / "assets").mkdir(parents=True, exist_ok=True)
        for name, content in restored_assets.items():
            destination = LIBRARY / "assets" / name
            if not destination.exists():
                temporary = destination.with_suffix(destination.suffix + ".restore")
                temporary.write_bytes(content)
                temporary.replace(destination)
        for a in data["attempts"]:
            old = db.execute("SELECT updated FROM attempts WHERE id=?", (a["id"],)).fetchone()
            if old is None or old[0] < a["updatedAt"]:
                db.execute("INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET updated=excluded.updated,payload=excluded.payload", (a["id"], a["updatedAt"], json.dumps(a, ensure_ascii=False)))
                restored += 1
    return {"restored": restored}


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
