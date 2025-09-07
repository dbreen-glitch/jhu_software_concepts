import re, time, random
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

http = urllib3.PoolManager()
HEADERS = {"User-Agent": "Mozilla/5.0"}
RESULT_RE = re.compile(r"/result/(\d+)$")   # captures the numeric id at end

def collect_result_links(survey_base: str, start_page: int = 1, end_page: int| None = None,
                         limit: int| None = None, page_param: str = "page", delay=(0.8, 1.5)):
    """
    Returns a list of (result_id, absolute_url) found on survey list pages.
    Duplicates are removed by id while preserving order.
    """
    seen_ids = set()
    links = []

    page = start_page
    while True:
        if end_page is not None and page > end_page:
            break

        page_url = f"{survey_base.rstrip('/')}/?{page_param}={page}"
        r = http.request("GET", page_url, headers=HEADERS, timeout=20.0)
        if r.status != 200:
            # stop or continue based on your preference
            # print(f"[warn] {page_url} -> {r.status}, skipping")
            page += 1
            continue

        soup = BeautifulSoup(r.data, "html.parser")

        # Narrow to result rows if you want (optional, but nice):
        # rows = soup.select("tr.tw-border-none")
        # anchors = [a for row in rows for a in row.select('a[href*="/result/"]')]

        # Simple, robust: get any /result/<id> link on the page
        anchors = soup.select('a[href^="/result/"], a[href*="/result/"]')

        new_on_this_page = 0
        for a in anchors:
            href = a.get("href") or ""
            m = RESULT_RE.search(href)
            if not m:
                continue
            rid = m.group(1)
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            abs_url = urljoin(survey_base, href)
            links.append((rid, abs_url))
            new_on_this_page += 1

            if limit is not None and len(links) >= limit:
                return links

        # Optional: stop when a page yields nothing (useful if pages are finite)
        # if found_on_this_page == 0:
        #     break

        time.sleep(random.uniform(*delay))  # be polite
        page += 1

    return links

if __name__ == "__main__":
    BASE = "https://www.thegradcafe.com/survey/"
    results = collect_result_links(BASE, start_page=1, limit=20)
    print(len(results))
    print(results[:15])  # show first few