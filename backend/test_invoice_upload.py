import asyncio
import httpx
import os

API_URL = "http://localhost:8001"
PDF_PATH = "/Users/kaushikrayadurga/Downloads/INV-CHR-040.pdf"

async def login(email, password):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            return r.json()["token"]
        return None

async def main():
    client_token = await login("client.admin@acmeco.dev", "TestPass123!")
    fwd_token = await login("fwd.admin@fastfreight.dev", "TestPass123!")
    
    headers_client = {"Authorization": f"Bearer {client_token}"}
    headers_fwd = {"Authorization": f"Bearer {fwd_token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Create Quote
        print("Creating Quote...")
        quote_payload = {
            "buyer_id": 4, # AcmeCo Logistics
            "origin_airport_id": 1,
            "destination_airport_id": 2,
            "tracking_number": "TRK-INV-123",
            "gross_weight": 100.0,
            "volumetric_weight": 120.0,
            "chargeable_weight": 120.0,
            "currency_id": 1,
            "charges": [
                {"raw_charge_name": "Freight", "rate": 5.0, "basis": "Per KG", "qty": 120.0, "amount": 600.0}
            ]
        }
        r = await client.post(f"{API_URL}/quotes", headers=headers_fwd, json=quote_payload)
        quote_id = r.json()["id"]
        
        # 2. Accept Quote
        print(f"Accepting Quote {quote_id}...")
        r = await client.patch(f"{API_URL}/quotes/{quote_id}/status", headers=headers_client, json={"status": "ACCEPTED"})
        
        # 3. Upload Invoice
        print("Uploading Invoice using tracking number (this will take a few seconds due to Veryfi and R2)...")
        with open(PDF_PATH, "rb") as f:
            files = {"file": ("INV-CHR-040.pdf", f, "application/pdf")}
            data = {"tracking_number": "TRK-INV-123"}
            r = await client.post(f"{API_URL}/invoices/upload", headers=headers_fwd, files=files, data=data)
        
        if r.status_code != 201:
            print("Upload failed:", r.status_code, r.text)
            return
            
        invoice = r.json()
        print("Upload successful!")
        print(f"Invoice Number: {invoice['invoice_number']}")
        print(f"R2 URL: {invoice['file_path']}")
        print(f"Extracted Charges count: {len(invoice['charges'])}")
        
        if len(invoice['charges']) > 0:
            charge_id = invoice['charges'][0]['id']
            # 4. Correct mapping
            print(f"Correcting mapping for invoice charge {charge_id}...")
            r = await client.patch(f"{API_URL}/invoices/charges/{charge_id}/mapping", headers=headers_client, json={
                "mapped_charge_id": 7 # Fuel Surcharge
            })
            print("Mapping correction:", r.status_code)

asyncio.run(main())
