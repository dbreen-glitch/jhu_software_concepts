"""Requirements for Module 4 - Analysis Formatting

a. Test labels & Rounding
i. Test that your page include “Answer” labels for rendered analysis
ii. Test that any percentage is formatted with two decimals.

"""

# tests/test_analysis_format.py
import re
import pytest
import app as app_module


@pytest.fixture
def app(monkeypatch):
    # Keep DB inert for render-only tests
    monkeypatch.setattr(
        app_module,
        "get_conn",
        lambda: type("C", (), {
            "__enter__": lambda s: s,
            "__exit__": lambda s, *a: False,
            "cursor": lambda s: type("K", (), {
                "__enter__": lambda s: s,
                "__exit__": lambda s, *a: False,
                "execute": lambda *a, **k: None,
                "fetchone": lambda : (1,)  # simple scalar so template can render
            })()
        })()
    )
    application = app_module.app
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


# 3a.i — Page includes “Answer” labels for rendered analysis
def test_page_includes_answer_labels(client):
    resp = client.get("/")
    html = resp.get_data(as_text=True)
    assert "Answer:" in html, "Expected at least one 'Answer:' label on the page"


# 3a.ii — Any percentage is formatted with two decimals
def test_percentages_formatted_two_decimals(client):
    resp = client.get("/")
    html = resp.get_data(as_text=True)

    # Check the common percentage lines use two decimals (e.g., 20.00, 40.00)
    patterns = [
        r"Percent[^:\n]*:\s*([0-9]+\.[0-9]{2})",
        r"Acceptance percent[^:\n]*:\s*([0-9]+\.[0-9]{2})",
    ]

    found_any = False
    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE)
        if m:
            found_any = True
            assert re.fullmatch(r"[0-9]+\.[0-9]{2}", m.group(1)), \
                "Expected percentage value to have exactly two decimals"

    # If your template only has one of the lines above, this still passes.
    assert found_any, "Expected at least one percentage value on the page to validate"
