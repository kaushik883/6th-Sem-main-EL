import asyncio
from veryfi import Client
from app.core.config import settings
import datetime

def get_client() -> Client:
    return Client(
        client_id=settings.VERYFI_CLIENT_ID,
        client_secret=settings.VERYFI_CLIENT_SECRET,
        username=settings.VERYFI_USERNAME,
        api_key=settings.VERYFI_API_KEY,
    )

async def extract_invoice_data(file_path: str) -> dict:
    """
    Extracts invoice data asynchronously using Veryfi.
    Returns normalized dict:
    {
        "invoice_number": str,
        "date": str,
        "line_items": [
            {"description": str, "price": float, "quantity": float, "total": float}
        ]
    }
    """
    client = get_client()
    
    # Run synchronous Veryfi call in a thread pool
    response = await asyncio.to_thread(
        client.process_document,
        file_path=file_path,
        categories=["Freight invoice"]
    )
    
    # Normalize Output
    inv_num = response.get("invoice_number")
    if not inv_num:
        # Fallback if Veryfi fails to extract invoice number
        inv_num = f"INV-{int(datetime.datetime.now().timestamp())}"
        
    extracted = {
        "invoice_number": str(inv_num),
        "date": response.get("date") or datetime.date.today().isoformat(),
        "line_items": []
    }
    
    for item in response.get("line_items", []):
        desc = item.get("description") or "Unknown Charge"
        # Strip basis suffixes that Veryfi sometimes concatenates into the description
        # e.g. "Security Surcharge Per Chg Wt" → "Security Surcharge"
        import re
        desc = re.sub(
            r'\s+(Per\s+Chg\s+Wt|Per\s+KG|Per\s+Shipment|Per\s+CBM|Per\s+Piece|Per\s+Unit|Per\s+Pkg|Per\s+Pallet|Per\s+Ton|Per\s+Lb|Per\s+Lbs|Per\s+Consignment)\s*$',
            '',
            desc,
            flags=re.IGNORECASE
        ).strip()
        
        # Parse numbers safely
        try:
            price = float(item.get("price") or 0.0)
        except ValueError:
            price = 0.0
            
        try:
            qty = float(item.get("quantity") or 1.0)
        except ValueError:
            qty = 1.0
            
        try:
            total = float(item.get("total") or 0.0)
        except ValueError:
            total = price * qty
            
        # Fallback: if price is 0 but total is provided, calculate price
        if price == 0.0 and total > 0.0:
            price = total / qty if qty > 0 else total
            
        extracted["line_items"].append({
            "description": desc,
            "price": price,
            "quantity": qty,
            "total": total
        })
        
    return extracted
