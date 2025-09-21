from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()

class Template(Base):
    __tablename__ = 'templates'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String, nullable=False)
    page_name = Column(String)
    base64_image = Column(String, nullable=False)
    caption = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_name': self.agent_name,
            'page_name': self.page_name,
            'caption': self.caption,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def delete_templates(cls, session, agent_name: str = None, page_name: str = None) -> int:
        """
        Delete templates from database based on optional filters
        
        Args:
            session: SQLAlchemy session
            agent_name: Optional agent name to filter deletions
            page_name: Optional page name to filter deletions
            
        Returns:
            Number of records deleted
        """
        query = session.query(cls)
        
        if agent_name:
            query = query.filter(cls.agent_name == agent_name)
        if page_name:
            query = query.filter(cls.page_name == page_name)
            
        count = query.count()  # Get count before deletion
        query.delete()
        
        return count

class Page(Base):
    """Model for storing full screenshots/pages"""
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)
    name = Column(String)  # Page name
    base64_image = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_name': self.agent_name,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Create engine
DB_PATH = Path(__file__).parent / 'template_database.db'
engine = create_engine(f'sqlite:///{DB_PATH}')

# Create session maker
Session = sessionmaker(bind=engine)

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")

# Create tables on import
try:
    create_tables()
except Exception as e:
    logger.warning(f"Could not create tables: {e}")

def delete_templates(agent_name: str = None, page_name: str = None) -> int:
    """
    Utility function to delete templates
    
    Args:
        agent_name: Optional agent name to filter deletions
        page_name: Optional page name to filter deletions
        
    Returns:
        Number of records deleted
    """
    try:
        with Session() as session:
            count = Template.delete_templates(session, agent_name, page_name)
            session.commit()
            logger.info(f"Deleted {count} templates" + 
                       (f" for agent '{agent_name}'" if agent_name else "") +
                       (f" on page '{page_name}'" if page_name else ""))
            return count
    except Exception as e:
        logger.error(f"Error deleting templates: {e}")
        raise 