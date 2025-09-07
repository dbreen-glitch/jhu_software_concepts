from scrape import scrape_data


class clean_data:
    def __init__(self, data):
        self.data = data.combined
        self.clean()

    def clean(self):
        for record in self.data:
            # Clean text fields
            for key, val in list(record.items()):
                if isinstance(val, str):
                    record[key] = " ".join(val.split()).strip()

            rename_map = {
                "result_url": "url",
                "added_on": "date_added",
                "Decision": "status",
                "Institution": "university",
                "Program": "program",
                "Degree's Country of Origin": "US/International",
                "Degree Type": "Degree"
            }
            for old_key, new_key in rename_map.items():
                if old_key in record and new_key not in record:
                    record[new_key] = record.pop(old_key)






if __name__ == "__main__":
    data = scrape_data(limit=40)
    cleaned = clean_data(data)
    print(cleaned.data)  # print first two records