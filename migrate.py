"""
Database Migration Script
Run this file to create/update all database tables based on models.py
"""

from models import Base, engine, SessionLocal
from sqlalchemy import text, inspect
import sys

def check_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_existing_columns(table_name):
    """Get existing columns for a table"""
    inspector = inspect(engine)
    if inspector.has_table(table_name):
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return columns
    return []

def migrate():
    """Create or update all database tables"""
    try:
        print("\n🔄 Starting database migration...\n")
        
        # Check connection first
        if not check_connection():
            return False
        
        # Get all tables from models
        tables = Base.metadata.tables
        print(f"📋 Found {len(tables)} tables in models:")
        for table_name in tables:
            print(f"   - {table_name}")
        
        print("\n📊 Checking existing database structure...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Create all tables (this will only create missing ones)
        print("\n🔨 Creating/updating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Check what was created/updated
        print("\n✅ Migration completed successfully!\n")
        
        # Show table status
        print("📋 Current database tables:")
        for table_name in tables:
            if table_name in existing_tables:
                existing_cols = get_existing_columns(table_name)
                model_cols = [col.name for col in tables[table_name].columns]
                
                new_cols = set(model_cols) - set(existing_cols)
                if new_cols:
                    print(f"   ✨ {table_name}: Added columns: {', '.join(new_cols)}")
                else:
                    print(f"   ✓ {table_name}: Up to date")
            else:
                print(f"   ✨ {table_name}: Created new table")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def rollback():
    """Drop all tables (use with caution!)"""
    print("\n⚠️  WARNING: This will drop all tables!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        try:
            Base.metadata.drop_all(bind=engine)
            print("✅ All tables dropped successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to drop tables: {e}")
            return False
    else:
        print("❌ Rollback cancelled")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  NEXVA DATABASE MIGRATION TOOL")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        # Rollback mode
        rollback()
    else:
        # Normal migration
        success = migrate()
        
        if success:
            print("\n" + "=" * 60)
            print("  ✅ Migration completed successfully!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("  ❌ Migration failed!")
            print("=" * 60)
            sys.exit(1)

