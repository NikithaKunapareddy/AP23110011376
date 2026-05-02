import httpx
import asyncio
import json

async def test_api():
    auth_body = {
        'email': 'anikitha_kunapareddy@srmap.edu.in',
        'name': 'Kunapareddy Nikitha',
        'rollNo': 'AP23110011376',
        'accessCode': 'QkbpxH',
        'clientID': '7f1331dd-c33a-4e79-97e5-8d014932869a',
        'clientSecret': 'KbkdTVytDpmAmnUk'
    }
    
    async with httpx.AsyncClient() as client:
        # Get token
        print("Getting token...")
        auth_resp = await client.post('http://20.207.122.201/evaluation-service/auth', json=auth_body, timeout=10)
        print(f"Auth Status: {auth_resp.status_code}")
        auth_data = auth_resp.json()
        token = auth_data.get('access_token')
        print(f"Token: {token[:50]}...")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test vehicles endpoint
        print("\nGetting vehicles...")
        vehicle_resp = await client.get('http://20.207.122.201/evaluation-service/vehicles', headers=headers, timeout=10)
        print(f'Vehicles Status: {vehicle_resp.status_code}')
        data = vehicle_resp.json()
        print(f'Response keys: {list(data.keys())}')
        if 'vehicles' in data:
            print(f'Vehicle count: {len(data["vehicles"])}')
            if data['vehicles']:
                print(f'First vehicle: {data["vehicles"][0]}')

asyncio.run(test_api())
