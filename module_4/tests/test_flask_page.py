"""Requirements for Module 4 - Flask Page

a. Test app factory / Config: Assert a testable Flask app is created with required routes (e.g. should test each of your “/routes” that you establish in flask).
b. Test GET /analysis (page load)
i. Status 200.
ii. Page Contains both “Pull Data” and “Update Analysis” buttons
iii. Page text includes “Analysis” and at least one “Answer:”

"""

# tests/test_flask_page.py
import pytest
import re
import app as app_module

# ---- Lightweight DB fakes so index page can render without Postgres ----
class _FakeCursor:
    def execute(self, sql):
        self._last_sql = sql

    def fetchone(self):
        sql = (getattr(self, "_last_sql", "") or "").lower()

        # crude rules so the template has numbers to render
        if "count(" in sql:
            return (1,)  # any count -> 1
        if "avg(gpa)" in sql:
            return (3.5,)
        if "avg(gre_aw)" in sql:
            return (4.5,)
        if "avg(gre_v)" in sql:
            return (157.0,)
        if "avg(gre)" in sql:
            return (322.0,)

        return (0,)

    # context-manager support
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def cursor(self):
        return _FakeCursor()

    # context-manager support
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def app(monkeypatch):
    # Ensure get_conn() returns our fake connection
    monkeypatch.setattr(app_module, "get_conn", lambda: _FakeConn())

    app = app_module.app
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# 1a) App factory / Config: assert required routes exist
def test_routes_exist(app):
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    required = {"/", "/pull-data", "/update-analysis"}
    missing = required - routes
    assert not missing, f"Missing expected routes: {missing}"


# 1b) "GET /analysis (page load)" — your analysis page is the index route.
def test_analysis_page_load_status_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_analysis_page_has_buttons_and_text(client):
    resp = client.get("/")
    html = resp.get_data(as_text=True)

    # ii. Contains both buttons
    assert "Pull Data" in html, "Missing 'Pull Data' button"
    assert "Update Analysis" in html, "Missing 'Update Analysis' button"

    # iii. Page text includes “Analysis” and at least one “Answer:”
    assert re.search(r"Analysis", html, re.I), "Expected the word 'Analysis' on the page"
    assert "Answer:" in html, "Expected at least one 'Answer:' label on the page"
