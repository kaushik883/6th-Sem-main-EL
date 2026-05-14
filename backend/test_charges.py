import asyncio
import httpx

API_URL = "http://localhost:8001"

async def login(email, password):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            return r.json()["token"]
        return None

async def main():
    # Login as client admin
    client_admin_token = await login("client.admin@acmeco.dev", "TestPass123!")
    fwd_admin_token = await login("fwd.admin@fastfreight.dev", "TestPass123!")
    
    headers_client = {"Authorization": f"Bearer {client_admin_token}"}
    headers_fwd = {"Authorization": f"Bearer {fwd_admin_token}"}
    
    async with httpx.AsyncClient() as client:
        # Test 1: Forwarder gets 403 on GET
        r = await client.get(f"{API_URL}/charges", headers=headers_fwd)
        print("Fwd GET charges:", r.status_code) # Expect 403
        
        # Test 2: Client admin can create charge
        r = await client.post(f"{API_URL}/charges", headers=headers_client, json={
            "name": "Air Freight", "short_name": "AF"
        })
        print("Create Air Freight:", r.status_code, r.json().get("id"))
        af_id = r.json().get("id")
        
        r = await client.post(f"{API_URL}/charges", headers=headers_client, json={
            "name": "Fuel Surcharge", "short_name": "FSC"
        })
        print("Create Fuel Surcharge:", r.status_code, r.json().get("id"))
        
        # Test 3: Duplicate charge fails
        r = await client.post(f"{API_URL}/charges", headers=headers_client, json={
            "name": "Air Freight", "short_name": "AF2"
        })
        print("Create Duplicate Name:", r.status_code) # Expect 400
        
        # Test 4: Add alias
        if af_id:
            r = await client.post(f"{API_URL}/charges/{af_id}/aliases", headers=headers_client, json={
                "alias": "Airfreight"
            })
            print("Add Alias Airfreight:", r.status_code)
            
            # Test 5: Duplicate alias fails
            r = await client.post(f"{API_URL}/charges/{af_id}/aliases", headers=headers_client, json={
                "alias": "Airfreight"
            })
            print("Add Duplicate Alias:", r.status_code) # Expect 400

asyncio.run(main())
