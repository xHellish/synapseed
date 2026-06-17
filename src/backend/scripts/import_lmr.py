import os
import sys
import asyncio
import pandas as pd
from sqlalchemy import select

# Add the parent directory to sys.path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import get_db_session
from app.models.lmr import Lmr
from app.models.product import Product

async def main():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../output/lmr.csv"))
    print(f"Reading CSV from {csv_path}")
    df = pd.read_csv(csv_path)

    async with get_db_session() as session:
        # First, check products registrante
        result = await session.execute(select(Product).limit(5))
        products = result.scalars().all()
        for p in products:
            print(f"Product {p.numero_registro}: {p.nombre_comercial}, Registrante: {p.registrante}")

        # Import LMR
        # Drop existing LMR to avoid duplicates
        await session.execute(Lmr.__table__.delete())
        
        # Insert in chunks
        chunk_size = 1000
        records = df.to_dict('records')
        print(f"Total records to insert: {len(records)}")
        
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i+chunk_size]
            lmr_objects = []
            for row in chunk:
                lmr_objects.append(Lmr(
                    plaguicida=str(row['plaguicida']).strip() if pd.notna(row['plaguicida']) else "",
                    clase=str(row['clase']).strip() if pd.notna(row['clase']) else None,
                    cultivo=str(row['cultivo']).strip() if pd.notna(row['cultivo']) else "",
                    lmr_nac=str(row['lmr_-_nac']).strip() if pd.notna(row['lmr_-_nac']) else None,
                ))
            session.add_all(lmr_objects)
            await session.commit()
            print(f"Inserted {i + len(chunk)} records")
            
        print("Import complete!")

if __name__ == "__main__":
    asyncio.run(main())
