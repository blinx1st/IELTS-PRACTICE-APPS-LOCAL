import importlib.util
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('check_library',ROOT/'scripts/check_library.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)

def test_runtime_library_needs_no_source_pdf_or_preparation_cache():
    assert checker.missing_resources()==[]

def test_missing_audio_is_reported_without_touching_original_library(tmp_path):
    # Only metadata is needed to check that absent resources are named correctly.
    (tmp_path/'library/listening/tests').mkdir(parents=True)
    sample=ROOT/'library/listening/tests/cam20-listening-test1.json'
    shutil.copyfile(sample,tmp_path/'library/listening/tests'/sample.name)
    missing=checker.missing_resources(tmp_path)
    assert any('audio' in p and (p.endswith('.mp3') or p.endswith('.m4a')) for p in missing)
    assert any('cam13-test1.json' in p for p in missing)
