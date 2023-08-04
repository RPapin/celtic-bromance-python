from dotenv import dotenv_values
import requests


class DataApiService:
    API_BASE = "https://api.jsonbin.io/v3/b/"
    ENTRYLIST_BIN = "64cbd4279d312622a38b4575"
    HEADERS = ""

    def __init__(self):
        config = dotenv_values(".env")
        self.HEADERS = {
            'Content-Type': 'application/json',
            'X-Master-Key': config['BIN_API_KEY'],
            'X-Bin-Versioning': 'false'
        }

    def get_entry_list(self):
        r = requests.get(url=self.API_BASE + self.ENTRYLIST_BIN, headers=self.HEADERS)
        return r.json()["record"]


# das = DataApiService()
# das.get_entry_list()
