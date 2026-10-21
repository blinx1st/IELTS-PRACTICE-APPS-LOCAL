"""Check the run-ready library without PDF, OCR caches, or importing the server."""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]

def missing_resources(root=ROOT):
    library=root/'library';missing=set();audio=set()
    def require(path):
        if not path.is_file() or path.stat().st_size==0:missing.add(str(path.relative_to(root)))
    def refs(value):
        if isinstance(value,dict):
            url=value.get('url','')
            if url.startswith('/library-assets/'):require(library/'assets'/Path(url).name)
            if url.startswith('/library-audio/'):
                audio.add(Path(url).name)
            for v in value.values():refs(v)
        elif isinstance(value,list):
            for v in value:refs(v)
    require(library/'presentation.json');require(library/'listening/audio-manifest.json')
    for book in range(13,21):
        for test in range(1,5):
            for listening in [False,True]:
                base=library/'listening' if listening else library
                name=f'cam{book}-'+('listening-' if listening else '')+f'test{test}.json'
                for folder in (['tests','keys','transcripts'] if listening else ['tests','keys']):
                    path=base/folder/name;require(path)
                    if path.is_file():
                        try:refs(json.loads(path.read_text(encoding='utf-8')))
                        except (ValueError,KeyError,TypeError):missing.add(str(path.relative_to(root)))
    # Audio URLs use hashes; the files remain on disk as hash.mp3.
    for name in audio:
        asset=library/'audio'/name
        if not asset.suffix:asset=asset.with_suffix('.mp3')
        require(asset)
    require(root/'frontend/public/app-logo.png')
    return sorted(missing)

def ensure_library(root=ROOT):
    missing=missing_resources(root)
    if missing:
        details='\n'.join('  - '+p for p in missing[:12])
        raise SystemExit('Thiếu hoặc hỏng '+str(len(missing))+' tài nguyên thư viện:\n'+details+'\nHãy clone/download đầy đủ repository, sau đó chạy CAI_DAT_LAN_DAU.cmd lại. Không cần chép PDF nguồn.')
    return True

if __name__=='__main__':
    ensure_library()
    print('Library ready: 32 Reading tests, 32 Listening tests; all referenced assets present.')
