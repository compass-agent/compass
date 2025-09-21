#!/usr/bin/env python3
"""
Reset Database Script
Drops all existing tables and recreates them with the current schema.
This will delete all existing data - use only when safe to do so.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path so we can import compass modules
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from compass.database.models import Base, engine, DB_PATH
import logging

logger = logging.getLogger(__name__)

def reset_database():
    """Drop all tables and recreate them with current schema"""
    try:
        print(f"Database location: {DB_PATH}")
        
        # Drop all existing tables
        print("Dropping all existing tables...")
        Base.metadata.drop_all(engine)
        print("✓ All tables dropped")
        
        # Create all tables with current schema
        print("Creating tables with current schema...")
        Base.metadata.create_all(engine)
        print("✓ All tables created")
        
        print("\n🎉 Database reset completed successfully!")
        print("All tables have been recreated with the latest schema.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Resetting database...")
    print("⚠️  WARNING: This will delete ALL existing data!")
    
    # In production, you might want to add a confirmation prompt
    # For now, since the user confirmed it's safe, we'll proceed
    
    success = reset_database()
    if success:
        print("\nDatabase is ready with the new schema including:")
        print("- Agent table with general_tools and software_integrations columns")
        print("- Template table")
        print("- Page table")
    else:
        sys.exit(1)
