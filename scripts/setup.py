"""One-time Windows setup; all subsequent launches work without network access."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PIP_DISABLE_PIP_VERSION_CHECK": "1"}


def run(command):
    subprocess.run(command, cwd=ROOT, env=ENV, check=True)


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Cần Python 3.11 trở lên. Hãy cài từ python.org rồi chạy lại.")
    if not shutil.which('node'):
        portable = sorted((ROOT / '.runtime').glob('node-*/node.exe'))
        if portable:
            ENV['PATH'] = str(portable[-1].parent) + os.pathsep + ENV.get('PATH', '')
            os.environ['PATH'] = ENV['PATH']
    node = shutil.which("node")
    npm = shutil.which("npm.cmd") if os.name == "nt" else shutil.which("npm")
    if not node or not npm:
        raise SystemExit("Cần Node.js LTS (22.12 trở lên). Hãy cài từ nodejs.org rồi chạy lại.")
    print("[1/3] Chuẩn bị môi trường Python riêng...", flush=True)
    target = ROOT / ".venv"
    python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        venv.create(target, with_pip=True)
    print("[2/3] Cài các thành phần cần thiết...", flush=True)
    run([str(python), "-X", "utf8", "-m", "pip", "install", "--progress-bar", "off", "-r", "requirements.txt"])
    run([npm, "ci" if (ROOT / "package-lock.json").exists() else "install", "--no-audit", "--no-fund"])
    print("[3/3] Đóng gói giao diện dùng offline...", flush=True)
    run([npm, "run", "build"])
    print("\nĐã cài xong. Nhấp đúp MO_UNG_DUNG.cmd để bắt đầu.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Cài đặt chưa hoàn tất (mã {e.returncode}). Kiểm tra kết nối Internet rồi chạy lại.")
