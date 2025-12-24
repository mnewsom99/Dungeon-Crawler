import requests
import json

url = "http://localhost:5000/api/chat"
data = {"npc_index": 1, "message": "Hello"} # Assuming ID 1 exists (Elara is likely 1)

try:
    print(f"Sending POST to {url}...")
    res = requests.post(url, json=data)
    print(f"Status Code: {res.status_code}")
    print("Response Content:")
    print(res.text)
except Exception as e:
    print(f"Request failed: {e}")
