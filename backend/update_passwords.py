import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def update_passwords():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Update client@acme.com password to password123
        await conn.execute("""
            UPDATE profiles 
            SET password_hash = $1 
            WHERE email = $2
        """, 
            '$2b$12$tWXfLG5E6PnnfAB0pl4WnuE6Gp5amKZA4bTozVQ3A/qUNNyVcTNcC',
            'client@acme.com'
        )
        print(f"✅ Updated password for client@acme.com → password123")
        
        # Update forwarder@dhl.com password to password123
        await conn.execute("""
            UPDATE profiles 
            SET password_hash = $1 
            WHERE email = $2
        """, 
            '$2b$12$tWXfLG5E6PnnfAB0pl4WnuE6Gp5amKZA4bTozVQ3A/qUNNyVcTNcC',
            'forwarder@dhl.com'
        )
        print(f"✅ Updated password for forwarder@dhl.com → password123")
        
        # Also add super@admin.com
        existing = await conn.fetchval(
            "SELECT email FROM profiles WHERE email = $1",
            'super@admin.com'
        )
        
        if not existing:
            await conn.execute("""
                INSERT INTO profiles (id, email, name, password_hash, role, is_admin) 
                VALUES ($1, $2, $3, $4, $5, $6)
            """, 
                'super-admin-002',
                'super@admin.com',
                'Super Admin',
                '$2b$12$tWXfLG5E6PnnfAB0pl4WnuE6Gp5amKZA4bTozVQ3A/qUNNyVcTNcC',
                'super_admin',
                True
            )
            print(f"✅ Added user: super@admin.com → password123")
        else:
            await conn.execute("""
                UPDATE profiles 
                SET password_hash = $1 
                WHERE email = $2
            """, 
                '$2b$12$tWXfLG5E6PnnfAB0pl4WnuE6Gp5amKZA4bTozVQ3A/qUNNyVcTNcC',
                'super@admin.com'
            )
            print(f"✅ Updated password for super@admin.com → password123")
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(update_passwords())
