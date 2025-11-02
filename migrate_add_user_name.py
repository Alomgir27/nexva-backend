from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://admin:admin123@localhost:5432/products_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255)"))
    conn.commit()
    print("✅ Migration complete: Added 'name' column to users table")

