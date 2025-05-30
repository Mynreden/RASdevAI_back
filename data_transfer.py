import pandas as pd
from sqlalchemy import create_engine

src_db_url = "postgresql://postgres.ghskobldjvaxulgbddds:Qwertys1234Qwertys!@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
dst_db_url = "postgresql://airflow:airflow@164.90.167.226/StockService"

src_engine = create_engine(src_db_url)
dst_engine = create_engine(dst_db_url)

chunk_size = 1000
offset = 0
total_rows = None

with src_engine.connect() as conn:
    while True:
        query = f"SELECT * FROM news ORDER BY id LIMIT {chunk_size} OFFSET {offset}"
        chunk = pd.read_sql(query, conn)

        if chunk.empty:
            break

        chunk.to_sql("news", dst_engine, if_exists="append", index=False)
        print(f"{len(chunk)} строк обработано (offset: {offset})")
        
        offset += chunk_size
