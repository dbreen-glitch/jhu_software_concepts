from scrape import scrape_data
from clean import clean_data

def save_data(records, path: str = "applicant_data.json") -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data = scrape_data(limit=40)
    cleaned = clean_data(data)
    print(cleaned.data)  # print first two records
    save_data(cleaned.data, "cleaned_applicant_data.json")