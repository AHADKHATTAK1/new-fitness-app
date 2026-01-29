#!/usr/bin/env python3
"""
Manual Database Migration Script
Connects to Neon PostgreSQL and runs all required migrations
"""

import psycopg2
from psycopg2 import sql

# Database connection URL
DATABASE_URL = "postgresql://neondb_owner:npg_UdX8K1pgAVnv@ep-wild-pine-adrlnus4-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Migration SQL statements
MIGRATIONS = [
    ("Add members.birthday column", "ALTER TABLE members ADD COLUMN IF NOT EXISTS birthday DATE"),
    ("Add members.last_check_in column", "ALTER TABLE members ADD COLUMN IF NOT EXISTS last_check_in TIMESTAMP"),
    ("Add attendance.created_at column", "ALTER TABLE attendance ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ("Add attendance.emotion column", "ALTER TABLE attendance ADD COLUMN IF NOT EXISTS emotion VARCHAR(50)"),
    ("Add attendance.confidence column", "ALTER TABLE attendance ADD COLUMN IF NOT EXISTS confidence FLOAT"),
    ("Create body_measurements table", """
        CREATE TABLE IF NOT EXISTS body_measurements (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            weight FLOAT,
            body_fat FLOAT,
            chest FLOAT,
            waist FLOAT,
            arms FLOAT,
            notes TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """),
    ("Create member_notes table", """
        CREATE TABLE IF NOT EXISTS member_notes (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """),
]

def run_migrations():
    """Connect to database and run all migrations"""
    
    print("🔧 Starting Database Migration...")
    print(f"📡 Connecting to: {DATABASE_URL.split('@')[1].split('/')[0]}")
    print()
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!\n")
        
        # Run each migration
        success_count = 0
        for i, (description, sql_query) in enumerate(MIGRATIONS, 1):
            try:
                print(f"[{i}/{len(MIGRATIONS)}] {description}...", end=" ", flush=True)
                cursor.execute(sql_query)
                conn.commit()
                print("✅")
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg or "duplicate" in error_msg.lower():
                    print("ℹ️  (already exists)")
                    success_count += 1
                else:
                    print(f"❌")
                    print(f"   Error: {error_msg[:200]}")
                    conn.rollback()
        
        # Verify tables
        print("\n📊 Verifying database schema...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print("✅ Tables in database:")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Migration Complete! {success_count}/{len(MIGRATIONS)} operations successful")
        print("\n✅ You can now visit: https://fitness-mangement1211.onrender.com")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection Error: {str(e)}")
        print("\n💡 Check:")
        print("   • Internet connection")
        print("   • DATABASE_URL is correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("   GYM MANAGER - DATABASE MIGRATION TOOL")
    print("=" * 60)
    print()
    
    success = run_migrations()
    
    if success:
        print("\n✅ All done! Database is ready.")
    else:
        print("\n❌ Migration failed. Check errors above.")
    
    input("\nPress Enter to exit...")
