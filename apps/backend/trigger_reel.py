import requests

url = "http://127.0.0.1:8000/api/ingest/url"
data = {
    "url": "https://www.instagram.com/reel/dummy_agentic_ai/",
    "content_type": "instagram_reel",
}
try:
    r = requests.post(url, json=data)
    print(r.json())
except Exception as e:
    print(e)
