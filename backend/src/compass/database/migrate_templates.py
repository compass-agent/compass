import sqlite3
from datetime import datetime
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent

# Connect to both databases using relative paths
old_conn = sqlite3.connect(script_dir / 'template_database_jan_25.db')
new_conn = sqlite3.connect(script_dir / 'template_database.db')

old_cur = old_conn.cursor()
new_cur = new_conn.cursor()

# Get current timestamp
current_time = datetime.utcnow().isoformat()

try:
    # Get first occurrence of each unique caption, excluding 'Sample'
    old_cur.execute('''
        WITH RankedTemplates AS (
            SELECT 
                caption, 
                base64_image,
                ROW_NUMBER() OVER (PARTITION BY caption ORDER BY id) as rn
            FROM templates
            WHERE caption != 'Sample'
        )
        SELECT caption, base64_image 
        FROM RankedTemplates 
        WHERE rn = 1
    ''')
    templates = old_cur.fetchall()
    
    print(f"Found {len(templates)} unique templates to migrate")
    
    # Insert into new database without specifying ID (let it auto-increment)
    for template in templates:
        new_cur.execute('''
            INSERT INTO templates (caption, base64_image, page_name, agent_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template[0], template[1], 'PartDesign', 'FreeCAD', current_time, current_time))
    
    new_conn.commit()
    print("Migration completed successfully!")

except Exception as e:
    print(f"Error during migration: {e}")
    
finally:
    old_conn.close()
    new_conn.close() 