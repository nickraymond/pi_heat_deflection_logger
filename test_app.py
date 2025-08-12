import requests

BASE = "http://localhost:5000"

print("\n🔹 GET /api/data")
print(requests.get(f"{BASE}/api/data").json())

print("\n🔹 POST /api/start")
print(requests.post(f"{BASE}/api/start").json())

print("\n⌛ Wait a few seconds while data is logged...")

import time
time.sleep(5)

print("\n🔹 POST /api/stop")
print(requests.post(f"{BASE}/api/stop").json())

print("\n🔹 GET /api/history")
print(requests.get(f"{BASE}/api/history").json())

print("\n🔹 GET /api/export")
r = requests.get(f"{BASE}/api/export")
filename = r.headers.get("Content-Disposition", "").split("filename=")[-1]
with open(filename, 'wb') as f:
	f.write(r.content)
print(f"📁 CSV saved as: {filename}")
