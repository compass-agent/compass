"""
Migration script to convert template IDs from INTEGER to UUID strings
"""
import sqlite3
from pathlib import Path

def get_db_path():
    # Go up two levels from the current file and find the database
    return Path(__file__).parent.parent / 'template_database.db'

def migrate_to_uuid():
    db_path = get_db_path()
    print(f"Using database at: {db_path}")
    
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    try:
        # Temporarily disable foreign key constraints
        cursor.execute('PRAGMA foreign_keys=OFF')
        
        # Create temporary table with UUID as primary key
        cursor.execute('''
            CREATE TABLE templates_new (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                page_name TEXT,
                base64_image TEXT NOT NULL,
                caption TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("Created new table structure...")
        
        # Copy data from old table to new table, generating UUIDs
        cursor.execute('''
            INSERT INTO templates_new (
                id, agent_name, page_name, base64_image, caption, 
                created_at, updated_at
            )
            SELECT 
                hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || 
                substr(hex(randomblob(2)), 2) || '-' || 
                substr('89ab', abs(random()) % 4 + 1, 1) || 
                substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)),
                agent_name, page_name, base64_image, caption, 
                created_at, updated_at
            FROM templates
        ''')
        
        # Get the number of migrated rows
        cursor.execute('SELECT COUNT(*) FROM templates_new')
        migrated_count = cursor.fetchone()[0]
        print(f"Migrated {migrated_count} templates...")
        
        # Drop the old table
        cursor.execute('DROP TABLE templates')
        print("Dropped old table...")
        
        # Rename the new table to the original name
        cursor.execute('ALTER TABLE templates_new RENAME TO templates')
        print("Renamed new table...")
        
        # Re-enable foreign key constraints
        cursor.execute('PRAGMA foreign_keys=ON')
        
        # Commit the transaction
        conn.commit()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_to_uuid() 