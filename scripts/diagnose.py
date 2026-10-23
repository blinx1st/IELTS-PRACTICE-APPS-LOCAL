"""Offline, read-only checks; never opens an attempt or changes its timer."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

from build_state import ROOT, build_fingerprint, build_info, build_is_current, runtime_fingerprint
from check_library import missing_resources


def command(args):
    try:
        r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
        return r.stdout.strip() if r.returncode==0 else r.stderr.strip()
    except (OSError,subprocess.TimeoutExpired):return 'unavailable'


def diagnose():
    workspace=hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
    servers=[]
    for port in range(8765,8776):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.25) as response:info=json.load(response)
            if info.get('app')!='reading-room-local':continue
            servers.append({'url':f'http://127.0.0.1:{port}','thisFolder':info.get('workspace')==workspace,
                            'runningCodeMatches':info.get('fingerprint')==runtime_fingerprint(ROOT),
                            'runningBuild':info.get('uiBuildFingerprint')})
        except (OSError,ValueError):pass
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    missing=missing_resources(ROOT)
    portable=sorted((ROOT/'.runtime').glob('node-*/node.exe'))
    node=shutil.which('node') or (str(portable[-1]) if portable else 'node')
    dependencies={}
    for name in ('fastapi','starlette','pydantic','uvicorn'):
        try:dependencies[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:dependencies[name]='missing'
    return {'folder':str(ROOT),'commit':command(['git','rev-parse','--short','HEAD']),
            'python':sys.version.split()[0],'architecture':platform.machine(),
            'node':command([node,'--version']),'dependencies':dependencies,
            'buildCurrent':build_is_current(ROOT),'sourceFingerprint':build_fingerprint(ROOT),
            'builtFingerprint':build_info(ROOT).get('sourceFingerprint'),
            'logoSourceSha256':sha(ROOT/'frontend/public/app-logo.png'),
            'logoBuiltSha256':sha(ROOT/'dist/app-logo.png'),
            'missingResourceCount':len(missing),'missingResources':missing[:20],'servers':servers}


if __name__=='__main__':
    report=diagnose()
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['buildCurrent']:print('\nGiao diện chưa khớp mã nguồn: chạy CAI_DAT_LAN_DAU.cmd.')
    if any(s['thisFolder'] and not s['runningCodeMatches'] for s in report['servers']):
        print('\nDịch vụ đang chạy là bản cũ: DUNG_UNG_DUNG.cmd, rồi MO_UNG_DUNG.cmd.')
    if any(not s['thisFolder'] for s in report['servers']):
        print('\nCó app của thư mục khác đang chạy. Mở bằng MO_UNG_DUNG.cmd của đúng bản clone.')
