from pathlib import Path


def test_manual_twa_workflow_has_expected_outputs():
    text = Path('.github/workflows/twa-test-build.yml').read_text(encoding='utf-8')
    assert 'workflow_dispatch:' in text
    assert 'out/android.apk' in text
    assert 'out/assetlinks.json' in text
    assert 'TWA Test Build' in text
