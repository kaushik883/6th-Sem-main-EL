import asyncio
import asyncpg
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()

async def fix_passwords():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    salt = bcrypt.gensalt()
    new_hash = bcrypt.hashpw("password123".encode("utf-8"), salt).decode("utf-8")
    
    try:
        await conn.execute("UPDATE profiles SET password_hash = $1 WHERE email IN ('client@acme.com', 'forwarder@dhl.com', 'super@admin.com')", new_hash)
        print("✅ Fixed passwords for all users to password123")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(fix_passwords())
