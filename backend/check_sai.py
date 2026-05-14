import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_sai():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        user = await conn.fetchrow("SELECT * FROM profiles WHERE email = 'sai@gmail.com'")
        
        if user:
            print("\n📋 User: sai@gmail.com")
            print("-" * 80)
            print(f"ID: {user['id']}")
            print(f"Email: {user['email']}")
            print(f"Name: {user['name']}")
            print(f"Role: {user['role']}")
            print(f"Company ID: {user['company_id']}")
            print(f"Is Admin: {user['is_admin']}")
            print(f"Is Active: {user['is_active']}")
            print(f"Password Hash: {user['password_hash'][:50]}...")
            print("-" * 80)
        else:
            print("❌ User sai@gmail.com not found!")
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(check_sai())
