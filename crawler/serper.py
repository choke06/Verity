import os
import requests

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def serper_search(query, num_results=10):
    if not SERPER_API_KEY:
        print("[SERPER KEY MISSING]")
        return []

    url = "https://google.serper.dev/search"

    payload = {
        "q": query,
        "num": num_results
    }

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        data = res.json()

        return [
            r["link"]
            for r in data.get("organic", [])
            if "link" in r
        ]

    except Exception as e:
        print(f"[SERPER ERROR]: {e}")
        return []