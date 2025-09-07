# This tests the code for scraping one page from thegradcafe.com

import time, random
import urllib3
from bs4 import BeautifulSoup

URL = "https://www.thegradcafe.com/result/"  # use a real 'See More' URL you clicked
http = urllib3.PoolManager()

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_detail_fields(url: str, start, finish) -> dict:
    data_output = []
    for page in range(start, finish + 1):
        r = http.request("GET", f'{url}{page}', headers=HEADERS, timeout=30.0, preload_content=True)
        if r.status != 200:
            raise Exception(f"Request failed with status {r.status}")

        soup = BeautifulSoup(r.data, "html.parser")


        dls = []
        dls = soup.select("dl") #selects the list of details section

        result = {}
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

if __name__ == "__main__":
    start = 986420
    finish = 986999
    data = get_detail_fields(URL, start, finish)
    print(data)
    if not data:
        print("[debug] No dt/dd pairs found. Save the HTML and I’ll adjust selectors.")
    for record in data:
        for k, v in record.items():
            print(f"{k}: {v}")