from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parents[1]


@pytest.mark.skipif(not (ROOT/"results/research/manifest.json").exists(), reason="Run the research notebooks first")
def test_every_page_in_both_languages(monkeypatch):
    monkeypatch.setenv("BIST_RESULTS_DIR", str(ROOT/"results/research"))
    app = AppTest.from_file(str(ROOT/"app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.info
    for language in ["Türkçe", "English"]:
        app.sidebar.radio[0].set_value(language).run()
        for option in app.sidebar.radio[1].options:
            app.sidebar.radio[1].set_value(option).run()
            assert not app.exception, (language, option)
            assert app.info
