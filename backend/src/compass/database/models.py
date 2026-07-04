from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()

class Agent(Base):
    """Persisted Agent Hub configuration."""
    __tablename__ = 'agents'

    # Historical databases use agent_id as the physical column name. Keep the
    # Python attribute as `id` so the rest of the service can stay tidy.
    id = Column('agent_id', String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(String, default="")
    prompt = Column(String, default="")
    general_tools = Column(JSON, default=list)
    software_integrations = Column(JSON, default=list)
    configuration = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'agentId': self.id,
            'name': self.name,
            'description': self.description or "",
            'prompt': self.prompt or "",
            'generalTools': self.general_tools or [],
            'softwareIntegrations': self.software_integrations or [],
            'configuration': self.configuration or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_modified': self.updated_at.isoformat() if self.updated_at else None,
        }

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

# Create engine (writable location in production, module dir in development)
from compass.runtime_paths import get_template_db_path
DB_PATH = get_template_db_path()
engine = create_engine(f'sqlite:///{DB_PATH}')

# Create session maker
Session = sessionmaker(bind=engine)

# Create all tables
def _migrate_agents_table():
    """Bring older Agent Hub tables up to the current model shape."""
    inspector = inspect(engine)
    if 'agents' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('agents')}
    statements = []

    if 'agent_id' not in columns and 'id' in columns:
        statements.extend([
            "ALTER TABLE agents ADD COLUMN agent_id VARCHAR(36)",
            "UPDATE agents SET agent_id = id WHERE agent_id IS NULL",
        ])

    if 'configuration' not in columns:
        statements.extend([
            "ALTER TABLE agents ADD COLUMN configuration JSON",
            "UPDATE agents SET configuration = '{}' WHERE configuration IS NULL",
        ])

    if statements:
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
        logger.info("Migrated agents table schema")


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(engine)
    _migrate_agents_table()
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
