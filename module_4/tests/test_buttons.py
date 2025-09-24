"""Requirements for Module 4 - Buttons

a. Test POST /pull-data (or whatever you named the path posting the pull data request)
i. Returns 200
ii. Triggers the loader with the rows from the scraper (should be faked / mocked)
b. Test POST /update-analysis (or whatever you named the path posting the update analysis request)
i. Returns 200 when not busy
c. Test busy gating
i. When a pull is “in progress”, POST /update-analysis returns 409 (and performs no update).
ii. When busy, POST /pull-data returns 409

"""

# tests/test_buttons.py
import types
import pytest
import app as app_module

# ---------- Helpers / Fakes ----------

class ImmediateThread:
    """
    Drop-in stand-in for threading.Thread that runs the target immediately
    when .start() is called. Lets us assert the job was triggered without
    spinning real threads in tests.
    """
    def __init__(self, target=None, args=(), kwargs=None):
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.started = False

    def start(self):
        self.started = True
        if self.target:
            self.target(*self.args, **self.kwargs)

    def join(self, *a, **k):  # not needed, but keeps parity with real Thread
        return


@pytest.fixture
def app(monkeypatch):
    # Avoid touching a real DB anywhere in these tests
    monkeypatch.setattr(app_module, "get_conn", lambda: types.SimpleNamespace(
        __enter__=lambda s: s,
        __exit__=lambda s, *exc: False,
        cursor=lambda : types.SimpleNamespace(
            __enter__=lambda s: s,
            __exit__=lambda s, *exc: False,
            execute=lambda *_: None,
            fetchone=lambda : (1,)
        )
    ))
    application = app_module.app
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


# ============ 2a) POST /pull-data ============

def test_pull_data_returns_200_and_triggers_loader(client, monkeypatch):
    """
    a.i Returns 200
    a.ii Triggers the loader with the rows from the scraper (mocked)
    """
    # Arrange: make the background job run synchronously
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    # Fake "scraper rows" and capture what the loader receives
    scraped_rows = [{"id": 1}, {"id": 2}, {"id": 3}]
    received = {"rows": None}

    # Provide a fake loader the job should call
    def fake_load_rows(rows):
        received["rows"] = rows

    # Provide a fake scrape_job that simulates: rows = scrape(); load(rows)
    # We patch the job that the route triggers so we can assert the chain.
    def fake_scrape_job():
        # in a real app you'd call your scraper here
        rows = list(scraped_rows)
        fake_load_rows(rows)

    monkeypatch.setattr(app_module, "scrape_job", fake_scrape_job)

    # Act
    resp = client.post("/pull-data", follow_redirects=True)

    # Assert
    assert resp.status_code == 200, "Expected 200 after posting /pull-data"
    assert received["rows"] == scraped_rows, "Loader must receive rows produced by the scraper"


# ============ 2b) POST /update-analysis when NOT busy ============

def test_update_analysis_returns_200_when_not_busy(client, monkeypatch):
    """
    b.i Returns 200 when not busy
    """
    monkeypatch.setattr(app_module, "is_scraping", False, raising=False)
    resp = client.post("/update-analysis", follow_redirects=True)
    assert resp.status_code == 200, "Expected 200 when system is not busy"


# ============ 2c) Busy-state gating ============

def test_update_analysis_returns_409_when_busy_and_does_not_update(client, monkeypatch):
    """
    c.i When a pull is in progress, POST /update-analysis returns 409 and performs no update
    """
    # Simulate busy
    monkeypatch.setattr(app_module, "is_scraping", True, raising=False)

    # If your update route calls a function to recompute/refresh, guard it:
    updated = {"called": False}
    def fake_update_job():
        updated["called"] = True
    # Expose a symbol the route would call (adjust if your code uses another name)
    monkeypatch.setattr(app_module, "run_update_job", fake_update_job, raising=False)

    resp = client.post("/update-analysis")

    assert resp.status_code == 409, "Expected 409 Conflict while busy"
    assert not updated["called"], "Update must not run while busy"


def test_pull_data_returns_409_when_busy(client, monkeypatch):
    """
    c.ii When busy, POST /pull-data returns 409
    """
    monkeypatch.setattr(app_module, "is_scraping", True, raising=False)
    resp = client.post("/pull-data")
    assert resp.status_code == 409, "Expected 409 Conflict when a pull is already in progress"
