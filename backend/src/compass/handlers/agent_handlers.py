import logging
from flask_socketio import emit
from datetime import datetime

from compass.constants import DEFAULT_AGENT_TYPE
from compass.agent.agent import AgentService
from compass.database.models import Session, Agent, Template, Page

logger = logging.getLogger(__name__)

def register_agent_handlers(socketio, state_manager, training_agent):
    """Register all agent-related socket handlers"""
    
    @socketio.on('new_chat')
    def handle_new_chat(data):
        logger.info('Starting new chat')
        try:
            # Update state manager with new agent type
            agent_name = data.get('agent_name', DEFAULT_AGENT_TYPE)  # Use default from constants if not specified
            state_manager.update_state({'agentType': agent_name})
            
            # Reinitialize just the agent service
            agent_service = AgentService(state_manager)
            emit('chat_reset', {'status': 'success'})
        except Exception as e:
            logger.error(f"Error starting new chat: {e}", exc_info=True)
            emit('error', {'message': str(e)})

    @socketio.on('delete_page')
    def handle_delete_page(data):
        """Delete a specific page by ID"""
        try:
            page_id = data.get('pageId')
            if not page_id:
                emit('delete_page_result', {'success': False, 'message': 'Page ID required'})
                return
            
            with Session() as session:
                # Find the page
                page = session.query(Page).filter_by(id=page_id).first()
                if not page:
                    emit('delete_page_result', {'success': False, 'message': 'Page not found'})
                    return
                
                # Store page info for response
                page_info = {
                    'id': page.id,
                    'name': page.name,
                    'agent_name': page.agent_name
                }
                
                # Delete associated templates first (optional - cascade delete)
                templates_deleted = session.query(Template).filter_by(
                    agent_name=page.agent_name, 
                    page_name=page.name
                ).delete()
                
                # Delete the page
                session.delete(page)
                session.commit()
                
                logger.info(f"PAGES: deleted page {page_info['name']} (ID: {page_id}) and {templates_deleted} associated templates")
                emit('delete_page_result', {
                    'success': True, 
                    'pageId': page_id,
                    'page': page_info,
                    'templatesDeleted': templates_deleted,
                    'message': f'Page "{page_info["name"] or "Untitled"}" deleted successfully'
                })
                
        except Exception as e:
            logger.error(f"PAGE DELETE ERROR: {e}", exc_info=True)
            emit('delete_page_result', {'success': False, 'message': f'Failed to delete page: {str(e)}'})



    @socketio.on('agent_hub')
    def handle_agent_hub(data):
        """General handler for Agent Hub actions with real database operations"""
        try:
            action = (data or {}).get('action')
            logger.info(f"AGENT_HUB: action={action}")

            if action == 'list':
                with Session() as session:
                    agents = session.query(Agent).all()
                    agents_data = [agent.to_dict() for agent in agents]
                    logger.info(f"AGENT_HUB: emitting list with {len(agents_data)} agents")
                    emit('agent_hub_result', {'action': 'list', 'success': True, 'agents': agents_data})
                return

            if action == 'create':
                name = data.get('name', 'New Agent')
                description = data.get('description', '')
                prompt = data.get('prompt', '')
                general_tools = data.get('generalTools', [])
                software_integrations = data.get('softwareIntegrations', [])
                
                with Session() as session:
                    # Check if agent name already exists
                    existing = session.query(Agent).filter_by(name=name).first()
                    if existing:
                        emit('agent_hub_result', {'action': 'create', 'success': False, 'message': f'Agent with name "{name}" already exists'})
                        return
                    
                    new_agent = Agent(
                        name=name,
                        description=description,
                        prompt=prompt,
                        general_tools=general_tools,
                        software_integrations=software_integrations
                    )
                    session.add(new_agent)
                    session.commit()
                    
                    # Refresh to get computed properties
                    session.refresh(new_agent)
                    agent_data = new_agent.to_dict()
                    
                    logger.info(f"AGENT_HUB: created agent {name}")
                    emit('agent_hub_result', {'action': 'create', 'success': True, 'agent': agent_data})
                return

            if action == 'update':
                agent_id = data.get('agentId')
                if not agent_id:
                    emit('agent_hub_result', {'action': 'update', 'success': False, 'message': 'Agent ID required'})
                    return
                
                with Session() as session:
                    agent = session.query(Agent).filter_by(agent_id=agent_id).first()
                    if not agent:
                        emit('agent_hub_result', {'action': 'update', 'success': False, 'message': 'Agent not found'})
                        return
                    
                    # Update fields if provided
                    if 'name' in data:
                        # Check if new name conflicts with existing agent
                        existing = session.query(Agent).filter_by(name=data['name']).filter(Agent.agent_id != agent_id).first()
                        if existing:
                            emit('agent_hub_result', {'action': 'update', 'success': False, 'message': f'Agent with name "{data["name"]}" already exists'})
                            return
                        agent.name = data['name']
                    if 'description' in data:
                        agent.description = data['description']
                    if 'prompt' in data:
                        agent.prompt = data['prompt']
                    if 'generalTools' in data:
                        agent.general_tools = data['generalTools']
                    if 'softwareIntegrations' in data:
                        agent.software_integrations = data['softwareIntegrations']
                    
                    agent.updated_at = datetime.utcnow()
                    session.commit()
                    
                    # Refresh to get computed properties
                    session.refresh(agent)
                    agent_data = agent.to_dict()
                    
                    logger.info(f"AGENT_HUB: updated agent {agent.name}")
                    emit('agent_hub_result', {'action': 'update', 'success': True, 'agent': agent_data})
                return

            if action == 'delete':
                agent_id = data.get('agentId')
                if not agent_id:
                    emit('agent_hub_result', {'action': 'delete', 'success': False, 'message': 'Agent ID required'})
                    return
                
                with Session() as session:
                    agent = session.query(Agent).filter_by(agent_id=agent_id).first()
                    if not agent:
                        emit('agent_hub_result', {'action': 'delete', 'success': False, 'message': 'Agent not found'})
                        return
                    
                    # Store agent info for response
                    agent_name = agent.name
                    
                    # Delete all associated templates first
                    templates_deleted = session.query(Template).filter_by(agent_name=agent.name).delete()
                    
                    # Delete all associated pages
                    pages_deleted = session.query(Page).filter_by(agent_name=agent.name).delete()
                    
                    # Delete the agent
                    session.delete(agent)
                    session.commit()
                    
                    logger.info(f"AGENT_HUB: deleted agent {agent_name} with {pages_deleted} pages and {templates_deleted} templates")
                    emit('agent_hub_result', {
                        'action': 'delete', 
                        'success': True, 
                        'agentId': agent_id,
                        'pagesDeleted': pages_deleted,
                        'templatesDeleted': templates_deleted,
                        'message': f'Agent "{agent_name}" and all training data deleted successfully'
                    })
                return



            # Placeholder for import/export - will implement in Steps 4-5
            if action == 'import':
                import_data = data.get('importData')
                if not import_data:
                    emit('agent_hub_result', {'action': 'import', 'success': False, 'message': 'Import data required'})
                    return
                
                try:
                    # Parse the import data (should be the JSON content of .agent file)
                    if isinstance(import_data, str):
                        import json
                        parsed_data = json.loads(import_data)
                    else:
                        parsed_data = import_data
                    
                    # Validate required fields
                    required_fields = ['name', 'schemaVersion']
                    for field in required_fields:
                        if field not in parsed_data:
                            emit('agent_hub_result', {'action': 'import', 'success': False, 'message': f'Invalid agent file: missing {field} field'})
                            return
                    
                    # Check schema version compatibility
                    schema_version = parsed_data.get('schemaVersion', '1.0.0')
                    if schema_version not in ['1.0.0', '2.0.0']:
                        emit('agent_hub_result', {'action': 'import', 'success': False, 'message': f'Unsupported schema version: {schema_version}'})
                        return
                    
                    with Session() as session:
                        # Check if agent name already exists
                        existing_agent = session.query(Agent).filter_by(name=parsed_data['name']).first()
                        if existing_agent:
                            emit('agent_hub_result', {'action': 'import', 'success': False, 'message': f'Agent with name "{parsed_data["name"]}" already exists'})
                            return
                        
                        # Handle different schema versions
                        if schema_version == '2.0.0':
                            # New format
                            general_tools = parsed_data.get('generalTools', [])
                            software_integrations = parsed_data.get('softwareIntegrations', [])
                        else:
                            # Legacy format (1.0.0) - convert old structure to new
                            general_tools = []
                            software_integrations = []
                            
                            # Convert old tools format
                            old_tools = parsed_data.get('tools', {})
                            if old_tools.get('commandLine'):
                                general_tools.append({'id': 'commandLine', 'name': 'Command Line', 'config': {'access': 'full'}})
                            if old_tools.get('fileEditor'):
                                general_tools.append({'id': 'fileEditor', 'name': 'File Editor', 'config': {'rootDir': '', 'restricted': True}})
                            
                            # Convert old targetApps format
                            target_apps = parsed_data.get('targetApps', [])
                            if isinstance(target_apps, list):
                                for app in target_apps:
                                    software_integrations.append({
                                        'id': app,
                                        'name': app,
                                        'scripting': True,
                                        'desktop': old_tools.get('desktopControl', False),
                                        'config': {},
                                        'trainingStatus': 'configured'
                                    })
                            
                            # Handle legacy single targetApp field
                            if 'targetApp' in parsed_data and parsed_data['targetApp'] and not target_apps:
                                software_integrations.append({
                                    'id': parsed_data['targetApp'],
                                    'name': parsed_data['targetApp'],
                                    'scripting': True,
                                    'desktop': old_tools.get('desktopControl', False),
                                    'config': {},
                                    'trainingStatus': 'configured'
                                })
                        
                        # Create new agent
                        new_agent = Agent(
                            name=parsed_data['name'],
                            description=parsed_data.get('description', ''),
                            prompt=parsed_data.get('prompt', ''),
                            general_tools=general_tools,
                            software_integrations=software_integrations
                        )
                        
                        session.add(new_agent)
                        session.flush()  # Get the agent ID
                        
                        # Import pages
                        pages_imported = 0
                        if 'pages' in parsed_data and parsed_data['pages']:
                            for page_data in parsed_data['pages']:
                                if 'base64_image' in page_data:  # Only import if has image data
                                    new_page = Page(
                                        agent_name=new_agent.name,
                                        name=page_data.get('name', ''),
                                        base64_image=page_data['base64_image']
                                    )
                                    session.add(new_page)
                                    pages_imported += 1
                        
                        # Import templates
                        templates_imported = 0
                        if 'templates' in parsed_data and parsed_data['templates']:
                            for template_data in parsed_data['templates']:
                                if 'base64_image' in template_data:  # Only import if has image data
                                    new_template = Template(
                                        agent_name=new_agent.name,
                                        page_name=template_data.get('page_name', ''),
                                        base64_image=template_data['base64_image'],
                                        caption=template_data.get('caption', '')
                                    )
                                    session.add(new_template)
                                    templates_imported += 1
                        
                        # Commit all changes
                        session.commit()
                        
                        # Refresh to get computed properties
                        session.refresh(new_agent)
                        agent_data = new_agent.to_dict()
                        
                        logger.info(f"AGENT_HUB: imported agent {new_agent.name} with {pages_imported} pages and {templates_imported} templates")
                        emit('agent_hub_result', {
                            'action': 'import', 
                            'success': True, 
                            'agent': agent_data,
                            'message': f'Successfully imported agent "{new_agent.name}" with {pages_imported} pages and {templates_imported} templates'
                        })
                        return  # Add return statement to prevent fallback error
                        
                except json.JSONDecodeError as e:
                    emit('agent_hub_result', {'action': 'import', 'success': False, 'message': f'Invalid JSON format: {str(e)}'})
                    return
                except Exception as e:
                    logger.error(f"AGENT_HUB: Import error: {e}", exc_info=True)
                    emit('agent_hub_result', {'action': 'import', 'success': False, 'message': f'Import failed: {str(e)}'})
                    return

            if action == 'export':
                agent_id = data.get('agentId')
                if not agent_id:
                    emit('agent_hub_result', {'action': 'export', 'success': False, 'message': 'Agent ID required'})
                    return
                
                with Session() as session:
                    # Get the agent
                    agent = session.query(Agent).filter_by(agent_id=agent_id).first()
                    if not agent:
                        emit('agent_hub_result', {'action': 'export', 'success': False, 'message': 'Agent not found'})
                        return
                    
                    # Get all related pages and templates
                    pages = agent.get_pages(session)
                    templates = agent.get_templates(session)
                    
                    # Create complete export data structure
                    export_data = {
                        'schemaVersion': '2.0.0',  # Updated schema version for new structure
                        'agentId': agent.agent_id,
                        'name': agent.name,
                        'description': agent.description,
                        'prompt': agent.prompt,
                        'generalTools': agent.general_tools,
                        'softwareIntegrations': agent.software_integrations,
                        'createdAt': agent.created_at.isoformat() + 'Z' if agent.created_at else None,
                        'updatedAt': agent.updated_at.isoformat() + 'Z' if agent.updated_at else None,
                        'pagesCount': len(pages),
                        'templatesCount': len(templates),
                        'pages': [{
                            'id': page.id,
                            'name': page.name,
                            'base64_image': page.base64_image,
                            'created_at': page.created_at.isoformat() if page.created_at else None,
                            'updated_at': page.updated_at.isoformat() if page.updated_at else None
                        } for page in pages],
                        'templates': [{
                            'id': template.id,
                            'page_name': template.page_name,
                            'base64_image': template.base64_image,
                            'caption': template.caption,
                            'created_at': template.created_at.isoformat() if template.created_at else None,
                            'updated_at': template.updated_at.isoformat() if template.updated_at else None
                        } for template in templates]
                    }
                    
                    # Convert to JSON and create downloadable content
                    import json
                    import base64
                    json_str = json.dumps(export_data, indent=2)
                    
                    # Create a filename based on agent name
                    filename = f"{agent.name.replace(' ', '_')}.agent"
                    
                    # Encode as base64 for frontend download
                    base64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                    
                    logger.info(f"AGENT_HUB: exported agent {agent.name} with {len(pages)} pages and {len(templates)} templates")
                    emit('agent_hub_result', {
                        'action': 'export', 
                        'success': True, 
                        'agentId': agent_id,
                        'filename': filename,
                        'content': base64_data,
                        'agentData': export_data  # Also send the data for frontend use
                    })
                    return

            logger.warning(f"AGENT_HUB: unsupported action {action}")
            emit('agent_hub_result', {'action': action or 'unknown', 'success': False, 'message': 'Unsupported action'})
        except Exception as e:
            logger.error(f"AGENT_HUB ERROR: {e}", exc_info=True)
            emit('agent_hub_result', {'action': 'error', 'success': False, 'message': str(e)})
