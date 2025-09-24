"""Requirements:

a. End-to-end (pull -> update -> Render)
i. Inject a fake scraper that returns multiple records
ii. POST /pull-data succeeds and rows are in DB
iii. POST /update-analysis succeeds (when not busy)
iv. GET /analysis shows updated analysis with correctly formatted values
b. Multiple pulls
i. Running POST /pull-data twice with overlapping data remains consistent with uniqueness policy.

"""

# tests/test_integration_end_to_end.py
import re
import pytest
import app as app_module

# ---------------- In-memory DB double ----------------

class _MemTable:
    def __init__(self):
        self.rows = {}  # keyed by result_id

    def insert(self, row):
        rid = row.get("result_id")
        if rid in self.rows:
            return False
        self.rows[rid] = row
        return True

    def select_rows(self, where=None):
        rows = list(self.rows.values())
        if where is None:
            return rows
        return [r for r in rows if where(r)]

    def count(self, where=None):
        return len(self.select_rows(where))


def _parse_where(sql):
    """
    Super-light WHERE parser:
      - col = 'val' (supports multiple ORs on same col)
      - col IS NOT NULL
      - AND between terms
    Returns a predicate(row)->bool
    """
    s = " ".join(sql.lower().split())
    if " where " not in s:
        return None

    where = s.split(" where ", 1)[1]
    for stopper in (" group by ", " order by ", ";"):
        if stopper in where:
            where = where.split(stopper, 1)[0]

    equals = {}
    not_null = set()

    import re
    for col, val in re.findall(r"([a-z_]+)\s*=\s*'([^']*)'", where):
        equals.setdefault(col, set()).add(val)
    for col in re.findall(r"([a-z_]+)\s+is\s+not\s+null", where):
        not_null.add(col)

    def pred(row):
        for col, allowed in equals.items():
            if row.get(col) not in allowed:
                return False
        for col in not_null:
            if row.get(col) is None:
                return False
        return True

    return pred


class _FakeCursor:
    def __init__(self, table: _MemTable):
        self.table = table
        self._last_result = None
        self.description = None

    def execute(self, sql, params=None):
        text = " ".join(sql.strip().split())
        low = text.lower()

        # INSERT INTO applicants (...)
        if low.startswith("insert into applicants"):
            cols_part = text[text.find("(")+1:text.find(")")]
            cols = [c.strip() for c in cols_part.split(",")]
            vals = list(params or [])
            row = {cols[i]: vals[i] for i in range(len(cols))}
            self.table.insert(row)
            self._last_result = None
            self.description = None
            return

        # COUNT(*)
        if "select count(*) from applicants" in low:
            where = _parse_where(low)
            self._last_result = (self.table.count(where),)
            self.description = (("count", None, None, None, None, None, None),)
            return

        # AVG(x)
        import re
        m = re.search(r"select\s+avg\(\s*([a-z_]+)\s*\)\s+from\s+applicants", low)
        if m:
            col = m.group(1)
            where = _parse_where(low)
            rows = self.table.select_rows(where)
            vals = [r.get(col) for r in rows if r.get(col) is not None]
            avg = sum(vals)/len(vals) if vals else None
            self._last_result = (avg,)
            self.description = ((f"avg_{col}", None, None, None, None, None, None),)
            return

        # Fallback
        self._last_result = None
        self.description = None

    def fetchone(self):
        return self._last_result

    def __enter__(self): return self
    def __exit__(self, *exc): return False


class _FakeConn:
    def __init__(self, table: _MemTable):
        self.table = table
    def cursor(self):
        return _FakeCursor(self.table)
    def __enter__(self): return self
    def __exit__(self, *exc): return False


# ---------------- Helpers ----------------

class ImmediateThread:
    """Run the target immediately on .start() for deterministic tests."""
    def __init__(self, target=None, args=(), kwargs=None):
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
    def start(self):
        if self.target:
            self.target(*self.args, **self.kwargs)

def _method_for(app, path):
    """Prefer POST if the route allows it; otherwise fall back to GET."""
    for rule in app.url_map.iter_rules():
        if rule.rule == path:
            return "POST" if "POST" in rule.methods else "GET"
    return "GET"


# ---------------- Fixtures ----------------

@pytest.mark.integration
def memdb(monkeypatch):
    table = _MemTable()
    monkeypatch.setattr(app_module, "get_conn", lambda: _FakeConn(table))
    return table

@pytest.fixture
def app(memdb, monkeypatch):
    # make background job synchronous
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    # Fake scraper: multiple records
    sample = [
        {
            "result_id": "a1",
            "term": "Fall 2025",
            "status": "Accepted",
            "degree": "Masters",
            "llm_generated_program": "computer science",
            "llm_generated_university": "jhu",
            "us_or_international": "US",
            "gpa": 3.8, "gre": 320, "gre_v": 155, "gre_aw": 4.5,
        },
        {
            "result_id": "a2",
            "term": "Fall 2025",
            "status": "Rejected",
            "degree": "PhD",
            "llm_generated_program": "computer science",
            "llm_generated_university": "georgetown",
            "us_or_international": "International",
            "gpa": 3.2, "gre": 310, "gre_v": 152, "gre_aw": 4.0,
        },
        {
            "result_id": "a3",
            "term": "Fall 2025",
            "status": "Accepted",
            "degree": "Masters",
            "llm_generated_program": "computer science",
            "llm_generated_university": "University of California, Berkeley",
            "us_or_international": "International",
            "gpa": 3.9, "gre": 325, "gre_v": 158, "gre_aw": 4.0,
        },
    ]

    def scrape_job():
        with app_module.get_conn() as conn, conn.cursor() as cur:
            for rec in sample:
                cols = list(rec.keys())
                sql = f"INSERT INTO applicants ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})"
                cur.execute(sql, [rec[c] for c in cols])

    pytest.sample_rows = sample
    monkeypatch.setattr(app_module, "scrape_job", scrape_job)

    application = app_module.app
    application.config.update(TESTING=True)
    return application

@pytest.fixture
def client(app):
    return app.test_client()


# ---------------- Tests ----------------

# 5a — End-to-end (pull -> update -> render)
def test_end_to_end_pull_update_render(client, app, memdb):
    # ii) POST/GET /pull-data succeeds and rows are in DB
    method = _method_for(app, "/pull-data")
    if method == "POST":
        r = client.post("/pull-data", follow_redirects=True)
    else:
        r = client.get("/pull-data", follow_redirects=True)
    assert r.status_code == 200
    assert memdb.count() == len(pytest.sample_rows)

    # iii) POST/GET /update-analysis succeeds when not busy
    method = _method_for(app, "/update-analysis")
    if method == "POST":
        r2 = client.post("/update-analysis", follow_redirects=True)
    else:
        r2 = client.get("/update-analysis", follow_redirects=True)
    assert r2.status_code == 200

    # iv) GET /analysis (index) shows updated analysis with correctly formatted values
    page = client.get("/")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Analysis" in html
    assert "Answer:" in html
    # At least one percentage with two decimals (e.g., 20.00)
    assert re.search(r"\b\d+\.\d{2}\b", html), "Expected a percentage formatted with two decimals"


# 5b — Multiple pulls: uniqueness policy respected
def test_multiple_pulls_respect_uniqueness(client, app, memdb):
    method = _method_for(app, "/pull-data")
    do = client.post if method == "POST" else client.get

    do("/pull-data", follow_redirects=True)
    count1 = memdb.count()

    # Same dataset again should not add rows
    do("/pull-data", follow_redirects=True)
    count2 = memdb.count()

    assert count2 == count1, "Second pull with identical rows should not create duplicates"
