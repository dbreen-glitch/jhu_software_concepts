# tests/test_flask_page.py
import re
import pytest
from src import app as app_module

@pytest.fixture
def app(monkeypatch):
    # no real DB calls during render
    monkeypatch.setattr(app_module, "get_conn",
                        lambda: type("C", (), {
                            "__enter__": lambda s: s,
                            "__exit__": lambda s, *a: False,
                            "cursor": lambda s: type("K", (), {
                                "__enter__": lambda s: s,
                                "__exit__": lambda s, *a: False,
                                "execute": lambda *a, **k: None,
                                "fetchone": lambda : (1,)
                            })()
                        })())
    application = app_module.app
    application.config.update(TESTING=True)
    return application

@pytest.fixture
def client(app):
    return app.test_client()

# 1a) Required routes exist
def test_routes_exist(app):
    routes = {r.rule for r in app.url_map.iter_rules()}
    assert "/" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes

# 1b) GET /analysis (index page in this app)
def test_analysis_page_loads_and_has_required_text(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert re.search(r"Analysis", html, re.I)
    assert "Answer:" in html
