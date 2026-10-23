import importlib.util
import json
from pathlib import Path
import subprocess

import pytest
from scripts.build_state import build_fingerprint, build_is_current

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def edition(tmp_path):
    root=tmp_path/'clone with spaces';(root/'frontend/public').mkdir(parents=True)
    (root/'frontend/public/app-logo.png').write_bytes(b'logo')
    (root/'frontend/src.tsx').write_bytes(b'first line\r\nsecond line\r\n')
    (root/'dist/assets').mkdir(parents=True)
    (root/'dist/index.html').write_text('<script src="/assets/app.js"></script>')
    (root/'dist/assets/app.js').write_text('bundle')
    (root/'dist/app-logo.png').write_bytes(b'logo')
    return root


def stamp(root):
    (root/'dist/build-info.json').write_text(json.dumps({'sourceFingerprint':build_fingerprint(root)}))


def test_existing_dist_is_not_enough_to_reuse_a_build(edition):
    assert not build_is_current(edition)
    stamp(edition);assert build_is_current(edition)
    (edition/'frontend/src.tsx').write_text('new source')
    assert not build_is_current(edition)


def test_missing_bundle_or_old_logo_requires_rebuild(edition):
    stamp(edition);assert build_is_current(edition)
    (edition/'dist/app-logo.png').write_bytes(b'old logo')
    assert not build_is_current(edition)
    (edition/'dist/app-logo.png').write_bytes(b'logo')
    (edition/'dist/assets/app.js').unlink()
    assert not build_is_current(edition)


def test_fingerprint_survives_windows_checkout_and_matches_vite(edition):
    first=build_fingerprint(edition)
    (edition/'frontend/src.tsx').write_bytes(b'first line\nsecond line\n')
    assert build_fingerprint(edition)==first
    module=(ROOT/'scripts/build-state.mjs').as_uri()
    result=subprocess.run(['node','--input-type=module','-e',f"import {{buildFingerprint}} from '{module}'; console.log(buildFingerprint(process.argv[1]));",str(edition)],check=True,capture_output=True,text=True)
    assert result.stdout.strip()==first


def test_launcher_does_not_reuse_old_backend_after_update(edition,monkeypatch):
    # Importing the launcher does not import FastAPI or touch personal history.
    import sys
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('test_launcher',ROOT/'scripts/launch.py')
    launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
    monkeypatch.setattr(launcher,'ROOT',edition);monkeypatch.setattr(launcher,'DATA',edition/'data')
    monkeypatch.setattr(launcher,'WORKSPACE','this-folder')
    monkeypatch.setattr(launcher,'build_is_current',lambda root:True)
    monkeypatch.setattr(launcher,'runtime_fingerprint',lambda root:'new-code')
    monkeypatch.setattr(launcher,'health',lambda port:{'app':'reading-room-local','workspace':'this-folder','fingerprint':'old-code'})
    python=edition/'.venv/Scripts/python.exe';python.parent.mkdir(parents=True);python.touch()
    with pytest.raises(SystemExit,match='DUNG_UNG_DUNG.cmd'):launcher.launch(no_browser=True)
