import urllib3
from bs4 import BeautifulSoup

URL = "https://www.thegradcafe.com/result/986420"  # use a real 'See More' URL you clicked
http = urllib3.PoolManager()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_detail_fields(url: str) -> dict:
    r = http.request("GET", url, headers=HEADERS, timeout=30.0, preload_content=True)
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
        # also catch flat dt/dd siblings if present
        for dt in dl.find_all("dt", recursive=False):
            dd = dt.find_next_sibling("dd")
            if dt and dd:
                key = dt.get_text(strip=True)
                val = dd.get_text(" ", strip=True)
                if key and val:
                    result[key] = val

    return result

if __name__ == "__main__":
    data = get_detail_fields(URL)
    if not data:
        print("[debug] No dt/dd pairs found. Save the HTML and I’ll adjust selectors.")
    for k, v in data.items():
        print(f"{k}: {v}")
