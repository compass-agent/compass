from compass.database.models import Base, engine, delete_templates
import logging

logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database and create all tables"""
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        try:
            count = delete_templates()
            print(f"Cleared all templates ({count} records deleted)")
        except Exception as e:
            print(f"Error clearing templates: {e}")
    else:
        init_database()
        print("Database initialized successfully!")
        print("Use --clear flag to delete all records") 