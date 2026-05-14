from veryfi import Client
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Client(
    client_id=os.getenv("VERYFI_CLIENT_ID"),
    client_secret=os.getenv("VERYFI_CLIENT_SECRET"),
    username=os.getenv("VERYFI_USERNAME"),
    api_key=os.getenv("VERYFI_API_KEY"),
)

response = client.process_document(
    file_path="/Users/kaushikrayadurga/Downloads/INV-CHR-040.pdf",
    categories=["Freight invoice"],
)
print(json.dumps(response, indent=4))