#!/usr/bin/env python3
"""Simple database cleanup script - empties all tables and adds baseline agent"""

from compass.database.models import Session, Agent, Template, Page

def cleanup_database():
    """Empty all tables and add baseline agent"""
    with Session() as session:
        # Clear all tables
        print("Clearing all tables...")
        session.query(Template).delete()
        session.query(Page).delete()
        session.query(Agent).delete()
        
        # Add baseline agent
        baseline_agent = Agent(
            name="compass-base-agent",
            description="Generic baseline agent with no specific knowledge domain",
            prompt="You are a helpful AI assistant with general capabilities.",
            general_tools=[],
            software_integrations=[]
        )
        session.add(baseline_agent)
        
        # Add structural-engineer agent (matches backend constants.py)
        structural_agent = Agent(
            name="structural-engineer",
            description="Specialized agent for structural engineering tasks with SAP2000 integration",
            prompt="You are a structural engineering expert with access to SAP2000 software and desktop automation capabilities.",
            general_tools=[
                {"id": "fileEditor", "name": "File Editor"},
                {"id": "commandLine", "name": "Command Line"}
            ],
            software_integrations=[
                {
                    "id": "SAP2000", 
                    "name": "SAP2000",
                    "scripting": True,
                    "desktop": True
                }
            ]
        )
        session.add(structural_agent)
        
        session.commit()
        print("✓ Database cleaned and baseline agents added")

if __name__ == "__main__":
    cleanup_database()
