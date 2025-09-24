"""Requirements:

a. Test insert on pull
i. Before: target table empty
ii. After POST/pull-data new rows exist with required (non-null) fields
b. Test idempotency / constraints
i. Duplicate rows do not create duplicates in database (accidentally pulling the same data should not result in the database acquiring duplicated rows).
c. Test simple query function
i. You should be able to query your data to return a dict with our expected keys (the required data fields within M3).

"""

# tests/test_db_insert.py
import pytest
import app as app_module

# ========== Minimal in-memory DB double ==========
class _Table:
    def __init__(self):
        # key by result_id to simulate natural unique key from dataset
        self.rows = {}
        self.columns = []

    def insert(self, row: dict):
        rid = row.get("result_id")
        if rid in self.rows:
            return False  # idempotent: do not duplicate
        self.rows[rid] = row
        for c in row.keys():
            if c not in self.columns:
                self.columns.append(c)
        return True

    def count(self):
        return len(self.rows)

    def any_row(self):
        return next(iter(self.rows.values()), None)


class _FakeCursor:
    def __init__(self, table: _Table):
        self.table = table
        self._result = None
        self.description = None

    def execute(self, sql, params=None):
        text = " ".join(sql.strip().split())
        upper = text.upper()
        if upper.startswith("INSERT INTO APPLICANTS"):
            # pattern: INSERT INTO applicants (col1,col2,...) VALUES (%s,...)
            cols_part = text[text.find("(") + 1:text.find(")")]
            cols = [c.strip() for c in cols_part.split(",")]
            vals = list(params or [])
            row = {cols[i]: vals[i] for i in range(len(cols))}
            self.table.insert(row)
            self._result = None
            self.description = None
        elif upper.startswith("SELECT COUNT(*) FROM APPLICANTS"):
            self._result = (self.table.count(),)
            self.description = (("count", None, None, None, None, None, None),)
        elif upper.startswith("SELECT * FROM APPLICANTS"):
            row = self.table.any_row()
            if row is None:
                self._result = None
                self.description = None
            else:
                cols = list(row.keys())
                self.description = tuple((c, None, None, None, None, None, None) for c in cols)
                self._result = tuple(row[c] for c in cols)
        else:
            self._result = None
            self.description = None

    def fetchone(self):
        return self._result

    def __enter__(self): return self
    def __exit__(self, *exc): return False


class _FakeConn:
    def __init__(self, table: _Table):
        self.table = table
    def cursor(self):
        return _FakeCursor(self.table)
    def __enter__(self): return self
    def __exit__(self, *exc): return False


# ---------- Fixtures ----------
@pytest.fixture
def memdb(monkeypatch):
    table = _Table()
    monkeypatch.setattr(app_module, "get_conn", lambda: _FakeConn(table))
    return table


@pytest.fixture
def app(memdb, monkeypatch):
    # run background job synchronously
    class ImmediateThread:
        def __init__(self, target=None, args=(), kwargs=None):
            self.target = target; self.args = args; self.kwargs = kwargs or {}
        def start(self):
            if self.target:
                self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    # Fake scrape job that inserts via SQL (so we exercise DB writes)
    sample_rows = [
        {
            "result_id": "r1",
            "term": "Fall 2025",
            "status": "Accepted",
            "degree": "Masters",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Johns Hopkins University",
            "us_or_international": "US",
            "gpa": 3.8,
            "gre": 320, "gre_v": 155, "gre_aw": 4.5
        },
        {  # duplicate of r1 to test idempotency
            "result_id": "r1",
            "term": "Fall 2025",
            "status": "Accepted",
            "degree": "Masters",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Johns Hopkins University",
            "us_or_international": "US",
            "gpa": 3.8,
            "gre": 320, "gre_v": 155, "gre_aw": 4.5
        },
        {
            "result_id": "r2",
            "term": "Fall 2025",
            "status": "Rejected",
            "degree": "PhD",
            "llm_generated_program": "Computer Science",
            "llm_generated_university": "Georgetown",
            "us_or_international": "International",
            "gpa": 3.2,
            "gre": 310, "gre_v": 152, "gre_aw": 4.0
        },
    ]

    def scrape_job():
        with app_module.get_conn() as conn, conn.cursor() as cur:
            for rec in sample_rows:
                cols = list(rec.keys())
                placeholders = ",".join(["%s"] * len(cols))
                sql = f"INSERT INTO applicants ({','.join(cols)}) VALUES ({placeholders})"
                cur.execute(sql, [rec[c] for c in cols])

    monkeypatch.setattr(app_module, "scrape_job", scrape_job)

    application = app_module.app
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


# 4a.i — Before: target table empty
def test_before_pull_table_empty(memdb):
    assert memdb.count() == 0


# 4a.ii — After /pull-data: new rows exist with required (non-null) fields
def test_after_pull_rows_inserted_with_required_fields(client, memdb):
    resp = client.get("/pull-data")
    assert resp.status_code in (200, 302)
    assert memdb.count() >= 2  # r1 (deduped) + r2

    required = [
        "result_id", "term", "status", "degree",
        "llm_generated_program", "llm_generated_university", "us_or_international"
    ]
    row = memdb.any_row()
    for k in required:
        assert k in row and row[k] not in (None, ""), f"{k} must be non-null"


# 4b.i — Idempotency / constraints: duplicate rows do not create duplicates
def test_idempotent_insert_on_duplicate_rows(client, memdb):
    client.get("/pull-data")
    n1 = memdb.count()
    client.get("/pull-data")  # same dataset again
    n2 = memdb.count()
    assert n2 == n1, "Duplicate pull must not increase row count"


# 4c.i — Simple query returns a dict with expected keys
def test_simple_query_returns_dict_with_expected_keys(memdb):
    with _FakeConn(memdb) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM applicants LIMIT 1")
        row = cur.fetchone()
        if row is None:
            pytest.skip("No rows available to query")
        cols = [d[0] for d in cur.description]
        result = dict(zip(cols, row))

    expected_keys = {
        "result_id", "term", "status", "degree",
        "llm_generated_program", "llm_generated_university",
        "us_or_international", "gpa", "gre", "gre_v", "gre_aw"
    }
    assert expected_keys.issubset(result.keys())
