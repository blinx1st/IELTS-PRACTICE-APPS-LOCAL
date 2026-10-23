import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from build_state import build_is_current, runtime_fingerprint

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RUNTIME = DATA / "runtime.json"
WORKSPACE = hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]


def health(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=.5) as r:
            return json.load(r)
    except (OSError, ValueError):
        return {}


def stop():
    if not RUNTIME.exists():
        print("App hiện không chạy bằng công cụ khởi động.")
        return
    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    if health(runtime["port"]).get("workspace") != WORKSPACE:
        print("App đã dừng. Không tác động đến tiến trình khác.")
        RUNTIME.unlink(missing_ok=True)
        return
    request = urllib.request.Request(f"http://127.0.0.1:{runtime['port']}/api/shutdown", method="POST", headers={"X-Reading-Room-Token": runtime["token"]})
    with urllib.request.urlopen(request, timeout=3) as r:
        json.load(r)
    for _ in range(30):
        if not health(runtime["port"]):
            RUNTIME.unlink(missing_ok=True)
            print("Đã dừng Reading Room. Đáp án đã lưu vẫn ở trên máy.")
            return
        time.sleep(.2)
    print("Đã gửi yêu cầu dừng.")


def launch(no_browser=False):
    from check_library import ensure_library
    ensure_library()
    DATA.mkdir(exist_ok=True)
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists() or not build_is_current(ROOT):
        print("Giao diện chưa được build hoặc đã cũ so với mã nguồn. Đang cập nhật...", flush=True)
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/setup.py")], cwd=ROOT, check=True)
    port = None
    for candidate in range(8765, 8776):
        info = health(candidate)
        if info.get("app") == "reading-room-local" and info.get("workspace") == WORKSPACE:
            if info.get('fingerprint') != runtime_fingerprint(ROOT):
                raise SystemExit('Dịch vụ đang chạy là phiên bản cũ. Chạy DUNG_UNG_DUNG.cmd, sau đó MO_UNG_DUNG.cmd để nạp bản mới. Không xóa data/.')
            url = f"http://127.0.0.1:{candidate}"
            if not no_browser:
                webbrowser.open(url)
            print(url)
            return
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", candidate))
                port = candidate
                break
            except OSError:
                pass
    if port is None:
        raise SystemExit("Các cổng local 8765–8775 đều đang bận. Hãy thử lại sau.")
    token = secrets.token_urlsafe(32)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "READING_ROOM_SHUTDOWN_TOKEN": token}
    with (DATA / "server.log").open("ab") as log:
        proc = subprocess.Popen([str(python), "-X", "utf8", "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    RUNTIME.write_text(json.dumps({"pid": proc.pid, "port": port, "token": token}), encoding="utf-8")
    for _ in range(60):
        if proc.poll() is not None:
            raise SystemExit("Dịch vụ chưa khởi động được. Xem data/server.log để biết chi tiết.")
        if health(port).get("workspace") == WORKSPACE:
            url = f"http://127.0.0.1:{port}"
            if not no_browser:
                webbrowser.open(url)
            print(url)
            return
        time.sleep(.25)
    raise SystemExit("Khởi động quá lâu. Hãy xem data/server.log và thử lại.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        stop() if args.stop else launch(args.no_browser)
    except (OSError, subprocess.CalledProcessError, ValueError) as e:
        print("Không thực hiện được:", e)
        raise SystemExit(1)
