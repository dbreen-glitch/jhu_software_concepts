# - exposes BASE / SURVEY_BASE / RESULT_BASE as class constants
# - on instantiation runs the survey collector (limit passed into constructor),
#   then fetches details for each found result and merges them
# - stores results on the instance as .links, .data (detail records), and .combined

import re
import time
import random
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class scrape_data:
    # ---- class-level constants ----
    BASE = "https://www.thegradcafe.com"
    SURVEY_BASE = f"{BASE}/survey/"
    RESULT_BASE = f"{BASE}/result/"

    # ---- regexes as class attributes ----
    RESULT_RE = re.compile(r"/result/(\d+)\b")
    TERM_RE   = re.compile(r"\b(Spring|Summer|Fall|Winter)\s+\d{4}\b")
    DATE_RE   = re.compile(r"[A-Z][a-z]+ \d{1,2}, \d{4}")

    # ---- http client shared by instances ----
    _http = urllib3.PoolManager()
    _HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(self, limit: int | None = None):
        """
        Create a scraper instance which immediately:
         1) collects up to `limit` survey entries (if limit is None it will run pages until exhaustion)
         2) fetches detail pages for each collected result
         3) merges survey + detail into self.combined

        After init you can inspect:
          - self.links     -> list[dict] survey rows (result_id, result_url, date_added, term)
          - self.data      -> list[dict] detail rows (merged detail fields)
          - self.combined  -> list[dict] merged per-result entries (survey + detail)
        """
        # run the two-stage workflow as part of initialization
        self.links = self.collect_survey_entries(self.SURVEY_BASE, limit=limit)
        # fetch details for each link
        self.data = []
        for item in self.links:
            rid = item["result_id"]
            try:
                detail = self.get_detail_fields(self.RESULT_BASE, rid)
            except Exception as e:
                # preserve basic failure info and continue
                detail = {"result_id": rid, "detail_error": str(e)}
            # ensure the detail record is a dict; append to list
            if isinstance(detail, dict):
                self.data.append(detail)
            else:
                # if legacy function returned list, try to extract first entry
                if isinstance(detail, list) and detail:
                    self.data.append(detail[0])
                else:
                    self.data.append({"result_id": rid})

        # merge into combined list keyed by result_id (detail overwrites survey on conflicts)
        survey_map = {r["result_id"]: r for r in self.links}
        detail_map = {d.get("result_id"): d for d in self.data if d.get("result_id") is not None}

        self.combined = []
        for rid, srec in survey_map.items():
            drec = detail_map.get(rid, {})
            merged = {**srec, **drec}
            self.combined.append(merged)


##################################### survey list scraping ####################################


    def collect_survey_entries(
        self,
        survey_base: str,
        start_page: int = 1,
        end_page: int | None = None,
        limit: int | None = None,
        page_param: str = "page",
        delay: tuple[float, float] = (0.8, 1.6),
    ) -> list[dict]:
        """Return list of dicts with result_id, result_url, added_on, term from survey list pages."""
        seen: set[str] = set()
        rows_out: list[dict] = []

        page = start_page
        while True:
            if end_page is not None and page > end_page:
                break

            page_url = f"{survey_base.rstrip('/')}/?{page_param}={page}"
            r = self._http.request("GET", page_url, headers=self._HEADERS, timeout=30.0)
            if r.status != 200:
                # skip page and continue scanning (keeps crawling behavior similar to original)
                page += 1
                continue

            soup = BeautifulSoup(r.data, "html.parser")

            # iterate rows in the table body; this captures both main rows and the detail rows
            rows = soup.select("tbody tr")

            new_found = 0
            for tr in rows:
                # the *main* row has >= 3 <td>
                tds = tr.find_all("td", recursive=False)
                if len(tds) < 3:
                    # skip (these do not contain information we want)
                    continue

                a = tr.select_one('a[href*="/result/"]')
                if not a:
                    continue

                href = a.get("href") or ""
                m = self.RESULT_RE.search(href)
                if not m:
                    continue
                rid = m.group(1)
                if rid in seen:
                    continue
                seen.add(rid)
                abs_url = urljoin(survey_base, href)

                # Added On date (3rd td)
                added_on = None
                added_text = tds[2].get_text(" ", strip=True)
                mdate = self.DATE_RE.search(added_text)
                added_on = mdate.group(0) if mdate else (added_text or None)

                # Look for the following sibling detail row that contains chips/tags (term)
                term = None
                detail_row = tr.find_next_sibling("tr", class_="tw-border-none")
                if detail_row:
                    mterm = detail_row.find(string=self.TERM_RE)
                    if mterm:
                        term = mterm.strip()

                rows_out.append({
                    "result_id": rid,
                    "result_url": abs_url,
                    "added_on": added_on,
                    "term": term,
                })
                new_found += 1

                # stop early when we've collected the requested limit
                if limit is not None and len(rows_out) >= limit:
                    return rows_out

            # if no new rows found and no end_page specified, assume we've reached the end
            if new_found == 0 and end_page is None:
                break

            time.sleep(random.uniform(*delay))
            page += 1

        return rows_out


#################################### detail scraping ####################################


    def get_detail_fields(self, result_base: str, rid) -> dict:
        """
        Fetch detail page for `rid` and return a single dict of fields (result_id included).
        """
        url = f"{result_base.rstrip('/')}/{rid}"
        r = self._http.request("GET", url, headers=self._HEADERS, timeout=30.0, preload_content=True)
        if r.status != 200:
            raise Exception(f"Request failed with status {r.status} for {url}")

        soup = BeautifulSoup(r.data, "html.parser")

        result = {"result_id": rid}

        # Prefer the structured <dl> blocks first (dt->dd)
        dls = soup.select("dl")
        for dl in dls:
            # case A: each pair wrapped in a div
            for row in dl.find_all("div", recursive=False):
                dt = row.find("dt")
                dd = row.find("dd")
                if dt and dd:
                    key = dt.get_text(strip=True)
                    val = dd.get_text(" ", strip=True)
                    if key and val:
                        result[key] = val

        # Also capture GRE/score block under ul.tw-list-none (label span + value span)
        for li in soup.select("ul.tw-list-none > li"):
            spans = li.find_all("span")
            key = spans[0].get_text(strip=True).rstrip(":")
            val = spans[-1].get_text(strip=True)
            result[key] = val

        return result


############################################### Main script ###############################################


if __name__ == "__main__":
    # instantiate and run the workflow; only parameter is the limit
    scraper = scrape_data(limit=40)

    print("collected survey links:", len(scraper.links))
    print("collected detail records:", len(scraper.data))
    print("combined records:", len(scraper.combined))
    for record in scraper.combined:
        for k, v in record.items():
            print(f"{k}: {v}")

    # sample output
#print(scraper.combined)  # print first two combined records
