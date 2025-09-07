# This scrapes multiple pages from thegradcafe.com survey listings WORKING COPY

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


#################################### detail scraping ####################################


def get_detail_fields(url: str, rid) -> dict:
    data_output = []

    r = http.request("GET", f'{url}{rid}', headers=HEADERS, timeout=30.0, preload_content=True)
    if r.status != 200:
        raise Exception(f"Request failed with status {r.status}")

    soup = BeautifulSoup(r.data, "html.parser")


    dls = []
    dls = soup.select("dl") #selects the list of details section

    result = {"result_id": rid}
    for dl in dls:
        # many pages structure rows as <div><dt>…</dt><dd>…</dd></div>
        for row in dl.find_all("div", recursive=True): # Keeps searches to direct children of dl
            dt = row.find("dt")
            dd = row.find("dd")
            if dt and dd:
                key = dt.get_text(strip=True)
                val = dd.get_text(" ", strip=True)
                if key and val:
                    result[key] = val

    for li in soup.select("ul.tw-list-none > li"):
        spans = li.find_all("span")
        key = spans[0].get_text(strip=True).rstrip(":")
        val = spans[1].get_text(strip=True)
        result[key] = val

    if result:
        data_output.append(result)

    # time.sleep(random.uniform(*delay))
    
    return data_output


############################################### Main script ###############################################


if __name__ == "__main__":
    BASE = "https://www.thegradcafe.com/"
    survey_base = f"{BASE}survey/"
    result_base = f"{BASE}result/"
    links = collect_survey_entries(survey_base, start_page=1, limit=20)


    data = []
    for item in links:
        details = get_detail_fields(result_base, item["result_id"])
        data.extend(details)


    survey_keys = {d["result_id"]: d for d in links}
    details_keys = {d["result_id"]: d for d in data}
    combined = []
    for rid, sdata in survey_keys.items():
        ddata = details_keys.get(rid, {})
        combined.append({**sdata, **ddata})

    print(combined)
    print(len(combined), "records")
'''
    data = get_detail_fields(result_base, start, finish)
    print(data)
    if not data:
        print("[debug] No dt/dd pairs found. Save the HTML and I’ll adjust selectors.")
    for record in data:
        for k, v in record.items():
            print(f"{k}: {v}")
'''