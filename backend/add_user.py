import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_user():
    # Get database URL and convert from SQLAlchemy format to asyncpg format
    db_url = os.getenv('DATABASE_URL')
    # Remove the +asyncpg part
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Check if user already exists
        existing = await conn.fetchval(
            "SELECT email FROM profiles WHERE email = $1",
            'client@acme.com'
        )
        
        if existing:
            print(f"✅ User client@acme.com already exists")
        else:
            # Add the user
            await conn.execute("""
                INSERT INTO profiles (id, email, name, password_hash, role, company_id, is_admin) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                'client-user-002',
                'client@acme.com',
                'Client User',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0K3e',
                'client',
                1,
                True
            )
            print(f"✅ Added user: client@acme.com")
            print(f"   Password: password123")
        
        # Also add forwarder@dhl.com
        existing = await conn.fetchval(
            "SELECT email FROM profiles WHERE email = $1",
            'forwarder@dhl.com'
        )
        
        if existing:
            print(f"✅ User forwarder@dhl.com already exists")
        else:
            await conn.execute("""
                INSERT INTO profiles (id, email, name, password_hash, role, company_id, is_admin) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                'forwarder-user-002',
                'forwarder@dhl.com',
                'Forwarder User',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6k0K3e',
                'forwarder',
                2,
                True
            )
            print(f"✅ Added user: forwarder@dhl.com")
            print(f"   Password: password123")
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(add_user())
