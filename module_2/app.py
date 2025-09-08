from scrape import scrape_data
from clean import clean_data

def save_data(records, path: str = "applicant_data.json") -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data = scrape_data(limit=100)
    cleaned = clean_data(data)
    save_data(cleaned.data, "applicant_data.json")