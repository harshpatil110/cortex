import json

import requests
from supabase import create_client

SUPABASE_URL = "https://icbtfvqyfzatlkbhnnna.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_koCn-TBcoguv17X6apMsow_WImZlf56"
API_BASE = "http://localhost:8000"

sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
res = sb.auth.sign_in_with_password(
    {"email": "harshp4114@gmail.com", "password": "123456"}
)
token = res.session.access_token

memories = requests.get(
    f"{API_BASE}/api/memories", headers={"Authorization": f"Bearer {token}"}
).json()

print(json.dumps(memories, indent=2))
