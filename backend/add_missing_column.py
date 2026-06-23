import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def add_column():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Check if column already exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='quotes' AND column_name='telemetry_data'
            )
        """)
        
        if exists:
            print('✅ Column telemetry_data already exists')
        else:
            await conn.execute('ALTER TABLE quotes ADD COLUMN telemetry_data JSONB')
            print('✅ Added telemetry_data column to quotes table')
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(add_column())
