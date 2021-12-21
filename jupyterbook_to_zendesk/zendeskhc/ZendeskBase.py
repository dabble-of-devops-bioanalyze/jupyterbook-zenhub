import requests
import json
import sys
import time


class ZendeskError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return sys.repr(self.value)


class Base:
    session = requests.Session()

    def __del__(self):
        self.session.close()

    def get(self, url, email=None, password=None):
        self.session.auth = (email, password)
        response_raw = self.session.get(url)

        if response_raw.status_code == 429:
            time.sleep(response_raw.headers["Retry-After"])
            return get(url, email, password)
        else:
            if response_raw.headers["Content-Type"].startswith(
                "application/json"
            ):  # sometimes, its UTF-8 instead of utf-8
                response_json = json.loads(response_raw.content)

                return response_json

            else:

                return None

    def put(self, url, data, email=None, password=None):
        self.session.auth = (email, password)
        self.session.headers = {"Content-Type": "application/json"}
        response_raw = self.session.put(url, data)

        if response_raw.status_code == 429:
            time.sleep(response_raw.headers["Retry-After"])
            return self.put(url, data, email, password)
        else:
            if response_raw.headers["Content-Type"].startswith("application/json"):
                response_json = json.loads(response_raw.content)
                return response_json
            else:
                return None

    def post(self, url, data, email=None, password=None):
        self.session.auth = (email, password)
        self.session.headers = {"Content-Type": "application/json"}
        response_raw = self.session.post(url, data)

        if response_raw.status_code == 429:
            time.sleep(response_raw.headers["Retry-After"])
            return post(url, data, email, password)
        else:
            if response_raw.headers["Content-Type"].startswith("application/json"):
                response_json = json.loads(response_raw.content)
                return response_json
            else:
                return None

    def delete(self, url, email=None, password=None):
        self.session.auth = (email, password)
        response_raw = self.session.delete(url)
        if response_raw.status_code == 429:
            time.sleep(response_raw.headers["Retry-After"])
            return self.delete(url, data, email, password)
        elif response_raw.status_code == 204:  # HTTP Status for No Content
            return {"status_code": 204}
        elif response_raw.status_code == 404:  # HTTP Status for Not Found
            return {"status_code": 404}
        else:
            if response_raw.headers["Content-Type"].startswith("application/json"):
                response_json = json.loads(response_raw.content)
                return response_json
            else:
                return None
