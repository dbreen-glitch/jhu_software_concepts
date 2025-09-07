import re, time, random
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

http = urllib3.PoolManager()
HEADERS = {"User-Agent": "Mozilla/5.0"}

RESULT_RE = re.compile(r"/result/(\d+)\b")
TERM_RE   = re.compile(r"\b(Spring|Summer|Fall|Winter)\s+\d{4}\b")
DATE_RE   = re.compile(r"[A-Z][a-z]+ \d{1,2}, \d{4}")

def collect_survey_entries(
    survey_base: str,
    start_page: int = 1,
    end_page: int | None = None,
    limit: int | None = None,
    page_param: str = "page",
    delay: tuple[float, float] = (0.8, 1.6),
) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []

    page = start_page
    while True:
        if end_page is not None and page > end_page:
            break

        page_url = f"{survey_base.rstrip('/')}/?{page_param}={page}"
        r = http.request("GET", page_url, headers=HEADERS, timeout=30.0)
        if r.status != 200:
            page += 1
            continue

        soup = BeautifulSoup(r.data, "html.parser")
        rows = soup.select("tbody tr")

        new_found = 0
        for tr in rows:
            # main rows have >= 3 <td>
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 3:
                continue

            a = tr.select_one('a[href*="/result/"]')
            if not a:
                continue

            href = a.get("href") or ""
            m = RESULT_RE.search(href)
            if not m:
                continue
            rid = m.group(1)
            if rid in seen:
                continue
            seen.add(rid)
            abs_url = urljoin(survey_base, href)

            # Added On date
            added_on = None
            added_text = tds[2].get_text(" ", strip=True)
            mdate = DATE_RE.search(added_text)
            added_on = mdate.group(0) if mdate else (added_text or None)

            # Look ahead to detail row for term
            term = None
            detail_row = tr.find_next_sibling("tr", class_="tw-border-none")
            if detail_row:
                mterm = detail_row.find(string=TERM_RE)
                if mterm:
                    term = mterm.strip()

            out.append({
                "result_id": rid,
                "url": abs_url,
                "date_added": added_on,
                "term": term,
            })
            new_found += 1

            if limit is not None and len(out) >= limit:
                return out

        if new_found == 0 and end_page is None:
            break

        time.sleep(random.uniform(*delay))
        page += 1

    return out



if __name__ == "__main__":
    survey_base = "https://www.thegradcafe.com/survey/"
    links = collect_survey_entries(survey_base, start_page=1, limit=20)
    print(len(links), "rows")
    print(links)