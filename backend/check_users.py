import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_users():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        users = await conn.fetch("SELECT id, email, name, role, company_id, is_admin FROM profiles ORDER BY email")
        
        print("\n📋 All users in database:")
        print("-" * 80)
        for user in users:
            print(f"Email: {user['email']:<30} | Role: {user['role']:<15} | Admin: {user['is_admin']}")
        print("-" * 80)
        print(f"Total: {len(users)} users\n")
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(check_users())
