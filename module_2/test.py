# This tests the code for scraping one page from thegradcafe.com

import re

from bs4 import BeautifulSoup
import urllib3

URL = "https://www.thegradcafe.com/result/986380"
http = urllib3.PoolManager()



#resp = http.request("GET", url)
#html = resp.data.decode("utf-8")

#soup = BeautifulSoup(html, "html.parser")

#text = soup.get_text()
#spaceless_text = text.replace("\n", "")
#print(text)

def get_detail_fields(url: str) -> dict:
    r = http.request("GET", url,headers={"User-Agent": "Mozilla/5.0"})
    if r.status != 200:
        raise Exception(f"Request failed with status {r.status}")

    soup = BeautifulSoup(r.data, "html.parser")

    section = soup.select_one("div.tw-mt-6")
    if not section:
        return {}

    dl = section.find("dl")
    if not dl:
        return {}

    result = {}
    for row in dl.find_all("div", recursive=False):
        dt = row.find("dt")
        dd = row.find("dd")
        if not dt or not dd:
            continue
        key = dt.get_text(strip=True)       # label, e.g., "Institution"
        val = dd.get_text(" ", strip=True)  # value, e.g., "Wayne State University"
        result[key] = val

    return result

data = get_detail_fields(URL)
for k, v in data.items():
    print(f"{k}: {v}")