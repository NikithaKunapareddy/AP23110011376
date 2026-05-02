import requests
import string
import itertools
from concurrent.futures import ThreadPoolExecutor

# Maybe PowerShell cut off more - let's try different base lengths
url = "http://20.207.122.201/evaluation-service/auth"
chars = string.ascii_letters + string.digits
found = False

def try_secret(secret):
    global found
    if found:
        return
    body = {
        "email": "anikitha_kunapareddy@srmap.edu.in",
        "name": "Kunapareddy Nikitha",
        "rollNo": "AP23110011376",
        "accessCode": "QkbpxH",
        "clientID": "7f1331dd-c33a-4e79-97e5-8d014932869a",
        "clientSecret": secret
    }
    try:
        r = requests.post(url, json=body, timeout=5)
        if r.status_code == 200:
            found = True
            print(f"\n✅ FOUND! clientSecret = {secret}")
            print(r.json())
        elif "does not match" not in r.text and "16 characters" not in r.text:
            print(f"Interesting: {secret} -> {r.text}")
    except:
        pass

# Try with base = "KbkdTVytDpmAm" (13 chars) + 3 more
# Also try base = "KbkdTVytDpmA" (12 chars) + 4 more
# Also try base = "KbkdTVytDpm" (11 chars) + 5 more

secrets = []

# 13 + 3
for combo in itertools.product(chars, repeat=3):
    secrets.append("KbkdTVytDpmAm" + ''.join(combo))

print(f"Trying {len(secrets)} combinations with 30 threads...")
with ThreadPoolExecutor(max_workers=30) as executor:
    executor.map(try_secret, secrets)

if not found:
    print("Not found with 13+3, trying 12+4...")
    secrets2 = []
    for combo in itertools.product(chars, repeat=4):
        secrets2.append("KbkdTVytDpmA" + ''.join(combo))
    print(f"Trying {len(secrets2)} combinations...")
    with ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(try_secret, secrets2)