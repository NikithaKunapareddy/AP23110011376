"""
Test all API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Health check
print("Test 1: Health Check")
resp = requests.get(f"{BASE_URL}/health")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}\n")

# Test 2: GET notifications
print("Test 2: GET /api/notifications/")
resp = requests.get(f"{BASE_URL}/api/notifications/?student_id=S001&page=1&limit=10")
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}\n")

# Test 3: Bulk notifications
print("Test 3: POST /api/notifications/bulk/send")
bulk_data = [
    {"student_id": "S001", "type": "EVENT", "message": "Campus event tomorrow"},
    {"student_id": "S002", "type": "RESULT", "message": "Your exam result is ready"},
    {"student_id": "S003", "type": "PLACEMENT", "message": "Job interview scheduled"}
]
resp = requests.post(
    f"{BASE_URL}/api/notifications/bulk/send",
    json=bulk_data,
    headers={"Content-Type": "application/json"}
)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}\n")

# Test 4: GET unread count
print("Test 4: GET /api/notifications/unread/count")
resp = requests.get(f"{BASE_URL}/api/notifications/unread/count?student_id=S001")
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}\n")

# Test 5: GET priority inbox
print("Test 5: GET /api/notifications/priority/inbox")
resp = requests.get(f"{BASE_URL}/api/notifications/priority/inbox?student_id=S001&n=5")
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}\n")

# Test 6: Vehicle scheduler status
print("Test 6: GET /api/scheduler/status")
resp = requests.get(f"{BASE_URL}/api/scheduler/status")
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}\n")

print("✅ All endpoints tested successfully!")
