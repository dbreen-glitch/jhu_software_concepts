from bs4 import BeautifulSoup
import urllib3

url = "https://www.thegradcafe.com/survey/"
http = urllib3.PoolManager(headers={"User-Agent": "Mozilla/5.0"}) # For flexibility to pretend to be a browser



resp = http.request("GET", url)
html = resp.data.decode("utf-8")

soup = BeautifulSoup(html, "html.parser")

text = soup.get_text()
#spaceless_text = text.replace("\n", "")
print(text)

