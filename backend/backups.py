"""Disk-backed, portable archives; no complete audio archive is held in RAM."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile

from fastapi import HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from backend.scoring import question_map

ZIP_LIMIT = 2_000_000_000
EXPANDED_LIMIT = 4_000_000_000


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def export(rows, library):
    files = {}
    def collect(value):
        if isinstance(value, dict):
            for v in value.values(): collect(v)
        elif isinstance(value, list):
            for v in value: collect(v)
        elif isinstance(value, str):
            for prefix, folder in (('/library-assets/', 'assets'), ('/library-audio/', 'audio')):
                if value.startswith(prefix):
                    name = value[len(prefix):]
                    if Path(name).name != name or '\\' in name: raise HTTPException(422, 'Invalid asset path.')
                    p = library / folder / name
                    if not p.is_file(): raise HTTPException(409, 'Thiếu tài liệu cần sao lưu: ' + name)
                    files[folder + '/' + name] = p
    for a in rows: collect(a['testSnapshot'])
    fd, name = tempfile.mkstemp(suffix='.zip'); __import__('os').close(fd)
    try:
        manifest = {'format': 'reading-room', 'version': 2, 'attempts': rows,
                    'files': {n: digest(p) for n, p in files.items()}}
        with zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            z.writestr('reading-room-backup.json', json.dumps(manifest, ensure_ascii=False))
            for n, p in files.items(): z.write(p, n, compress_type=zipfile.ZIP_STORED if n.startswith('audio/') else zipfile.ZIP_DEFLATED)
        if Path(name).stat().st_size > ZIP_LIMIT: raise HTTPException(413, 'Bản sao lưu vượt 2 GB.')
        return FileResponse(name, media_type='application/zip', filename='reading-room-backup.zip',
                            background=BackgroundTask(Path(name).unlink, missing_ok=True))
    except Exception:
        Path(name).unlink(missing_ok=True)
        raise


async def import_archive(upload, library, connect, lock):
    with tempfile.TemporaryDirectory(prefix='reading-restore-') as temp:
        base = Path(temp); archive = base / 'backup.zip'; size = 0
        with archive.open('wb') as f:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > ZIP_LIMIT: raise HTTPException(413, 'Bản sao lưu vượt 2 GB.')
                f.write(chunk)
        try:
            with zipfile.ZipFile(archive) as z:
                if sum(i.file_size for i in z.infolist()) > EXPANDED_LIMIT: raise ValueError('Archive too large')
                info = z.getinfo('reading-room-backup.json')
                if info.file_size > 100_000_000: raise ValueError('Manifest too large')
                data = json.loads(z.read(info))
                if data['format'] != 'reading-room' or data['version'] not in (1, 2): raise ValueError('Format')
                rows = data['attempts']; assert isinstance(rows, list)
                files = data.get('files', {}) if data['version'] == 2 else {'assets/' + n: h for n, h in data.get('assets', {}).items()}
                for name, expected in files.items():
                    parts = name.split('/')
                    if len(parts) != 2 or parts[0] not in ('assets', 'audio') or not parts[1] or Path(parts[1]).name != parts[1] or '\\' in name:
                        raise ValueError('Path')
                    dest = base / name; dest.parent.mkdir(exist_ok=True)
                    with z.open(name) as src, dest.open('wb') as out: shutil.copyfileobj(src, out, 1024 * 1024)
                    if digest(dest) != expected: raise ValueError('Checksum')
                    existing = library / name
                    if existing.exists() and digest(existing) != expected: raise ValueError('Asset collision')
                for a in rows:
                    uuid.UUID(a['id'])
                    assert a['status'] in ('active', 'paused', 'submitted', 'graded')
                    assert isinstance(a['updatedAt'], (int, float)) and isinstance(a['answers'], dict)
                    assert set(map(str, a['numbers'])) <= set(question_map(a['testSnapshot']))
                    assert all(str(n) in a['keySnapshot']['answers'] for n in a['numbers'])
                    for n in ('revision', 'startedAt', 'deadline', 'duration', 'remaining', 'annotations', 'flags', 'testId', 'title', 'book', 'mode', 'currentPassage'): a[n]
                    if a['status'] == 'graded': assert isinstance(a['result']['rows'], list)
        except Exception:
            raise HTTPException(422, 'Tệp sao lưu không hợp lệ hoặc bị hỏng.')
        restored = 0
        with lock, connect() as db:
            for name in files:
                dest = library / name; dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists(): shutil.copyfile(base / name, dest)
            for a in rows:
                # A restored playback session must be resumed explicitly on this machine.
                if a.get('player'):
                    if a['player'].get('running'):
                        a['player'].update(interrupted=True, interruptions=a['player'].get('interruptions',0)+1)
                    a['player'].update(running=False, leaseOwner=None, leaseUntil=0)
                old = db.execute('SELECT updated FROM attempts WHERE id=?', (a['id'],)).fetchone()
                if old is None or old[0] < a['updatedAt']:
                    db.execute('INSERT INTO attempts VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET updated=excluded.updated,payload=excluded.payload',
                               (a['id'], a['updatedAt'], json.dumps(a, ensure_ascii=False)))
                    restored += 1
        return {'restored': restored}
