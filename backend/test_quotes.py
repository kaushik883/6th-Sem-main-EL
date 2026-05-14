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
    client_admin_token = await login("client.admin@acmeco.dev", "TestPass123!")
    fwd_admin_token = await login("fwd.admin@fastfreight.dev", "TestPass123!")
    
    headers_client = {"Authorization": f"Bearer {client_admin_token}"}
    headers_fwd = {"Authorization": f"Bearer {fwd_admin_token}"}
    
    async with httpx.AsyncClient() as client:
        # FWD: Submit Quote with "Airfreight" and "Random Fee"
        quote_payload = {
            "buyer_id": 1, # AcmeCo Logistics
            "origin_airport_id": 1,
            "destination_airport_id": 2,
            "tracking_number": "TRK-123",
            "gross_weight": 100.0,
            "volumetric_weight": 120.0,
            "chargeable_weight": 120.0,
            "currency_id": 1,
            "charges": [
                {"raw_charge_name": "Airfreight", "rate": 5.0, "basis": "Per KG", "qty": 120.0, "amount": 600.0},
                {"raw_charge_name": "Random Fee", "rate": 50.0, "basis": "Per Shipment", "qty": 1.0, "amount": 50.0}
            ]
        }
        
        r = await client.post(f"{API_URL}/quotes", headers=headers_fwd, json=quote_payload)
        quote = r.json()
        print("Quote Created:", r.status_code)
        
        af_charge = next(c for c in quote["charges"] if c["raw_charge_name"] == "Airfreight")
        rf_charge = next(c for c in quote["charges"] if c["raw_charge_name"] == "Random Fee")
        
        print("Auto-map Airfreight:", af_charge["mapped_charge_name"]) # Should be 'Air Freight'
        print("Auto-map Random Fee:", rf_charge["mapped_charge_name"]) # Should be None
        
        # CLIENT: Correct Random Fee
        r = await client.patch(f"{API_URL}/quotes/charges/{rf_charge['id']}/mapping", headers=headers_client, json={
            "mapped_charge_id": 7 # Fuel Surcharge
        })
        print("Manual Mapping Correction:", r.status_code)
        
        # FWD: Submit New Quote with "Random Fee"
        quote_payload["charges"] = [
            {"raw_charge_name": "Random Fee", "rate": 50.0, "basis": "Per Shipment", "qty": 1.0, "amount": 50.0}
        ]
        r = await client.post(f"{API_URL}/quotes", headers=headers_fwd, json=quote_payload)
        new_quote = r.json()
        
        rf_charge_new = next(c for c in new_quote["charges"] if c["raw_charge_name"] == "Random Fee")
        print("New Auto-map Random Fee:", rf_charge_new["mapped_charge_name"]) # Should be 'Fuel Surcharge'

asyncio.run(main())
