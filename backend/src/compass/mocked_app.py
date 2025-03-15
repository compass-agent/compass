import eventlet
import os

# Configure eventlet for debugging
if os.environ.get('FLASK_DEBUG') == '1':
    eventlet.monkey_patch(all=True, thread=False, os=True)  # Don't patch threading in debug mode
else:
    eventlet.monkey_patch(all=True, thread=True, os=True)

import signal
import sys
import logging
import asyncio
import json
import time
import random
import uuid
from datetime import datetime
from enum import Enum

# Configure logging before other imports
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask and SocketIO imports
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

# Define agent status and mode enums to match real app
class AgentStatus(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

class AgentMode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mock_secret_key'

# Initialize SocketIO with debug-specific settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    debug=True,
    async_handlers=False if os.environ.get('FLASK_DEBUG') == '1' else True
)

# Mock state for the application
mock_state = {
    'agent_type': 'FreeCAD',
    'mode': AgentMode.AUTO,
    'status': AgentStatus.STOPPED,
    'pending_tools': [],
    'conversation_history': []
}

# Define common mock responses for various tools
MOCK_TOOL_RESPONSES = {
    'computer': {
        'screenshot': {
            'content': 'Mock screenshot captured at 1920x1080 resolution', 
            'error': None,
            'image_data': 'data:image/png;base64,mock_image_data_here'
        },
        'click': {
            'content': 'Successfully clicked at position (x=100, y=200)', 
            'error': None
        },
        'type': {
            'content': 'Successfully typed: "example text"', 
            'error': None
        },
        'get_window_info': {
            'content': json.dumps({
                'activeWindow': 'FreeCAD',
                'allWindows': ['FreeCAD', 'Terminal', 'Browser'],
                'resolution': [1920, 1080]
            }),
            'error': None
        }
    },
    'bash': {
        'ls': {
            'content': 'file1.txt\nfile2.py\nREADME.md\nsrc/\nbin/', 
            'error': None
        },
        'pwd': {
            'content': '/home/user/project', 
            'error': None
        },
        'cat': {
            'content': 'This is the content of the requested file.\nIt contains multiple lines.\nThis is just mock data.', 
            'error': None
        },
        'error_example': {
            'content': '', 
            'error': 'Command not found: invalid_command'
        },
        'default': {
            'content': 'Mock bash command output\nOperation completed successfully', 
            'error': None
        }
    },
    'file': {
        'read': {
            'content': 'Mock file content from specified path\nLine 1\nLine 2\n# Example code or configuration', 
            'error': None
        },
        'write': {
            'content': 'Successfully wrote content to file at the specified path', 
            'error': None
        },
        'list': {
            'content': json.dumps([
                {'name': 'file1.txt', 'type': 'file', 'size': 1024},
                {'name': 'file2.py', 'type': 'file', 'size': 2048},
                {'name': 'docs', 'type': 'directory'}
            ]), 
            'error': None
        },
        'default': {
            'content': 'File operation completed successfully', 
            'error': None
        }
    }
}

# Store some mock conversation history to provide context
MOCK_CONVERSATIONS = {
    'FreeCAD': [
        {"role": "system", "content": "You are an AI assistant for FreeCAD."},
        {"role": "user", "content": "Can you help me design a simple box in FreeCAD?"},
        {"role": "assistant", "content": "I'll help you design a simple box in FreeCAD. Let's break this down into steps."}
    ],
    'OpenFOAM': [
        {"role": "system", "content": "You are an AI assistant for OpenFOAM."},
        {"role": "user", "content": "Can you help me set up a simple CFD simulation?"},
        {"role": "assistant", "content": "I'll guide you through setting up a basic CFD simulation in OpenFOAM."}
    ],
    'Generic': [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Can you help me with this project?"},
        {"role": "assistant", "content": "I'd be happy to help with your project. What specific aspects do you need assistance with?"}
    ]
}

# Mocked socket event handlers

def cleanup():
    """Cleanup function to handle graceful shutdown"""
    logger.info('Shutting down mock server gracefully...')
    try:
        socketio.stop()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
    finally:
        sys.exit(0)

def signal_handler(sig, frame):
    cleanup()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def emit_status_update():
    """Utility function to emit current status updates to clients"""
    socketio.emit('status_update', {
        'status': mock_state['status'],
        'mode': mock_state['mode'],
        'agentType': mock_state['agent_type'],
        'pendingTools': len(mock_state['pending_tools'])
    })

@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected with sid: {request.sid}')
    socketio.emit('status', {'data': 'Connected to mock server', 'sid': request.sid})
    # Send initial status upon connection
    emit_status_update()

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected with sid: {request.sid}')

@socketio.on('message')
def handle_message(data):
    try:
        logger.info("Handling new message in mock server")
        text = data.get('text', '')
        image_data = data.get('image_data')
        workflow_name = data.get('workflow_name')
        
        logger.info(f"Received message: {text[:50] if text else '(no text)'} with workflow: {workflow_name}")
        
        # Skip processing empty messages
        if not text and not image_data:
            logger.info("Skipping empty message")
            return
        
        # Add to mock conversation history
        mock_state['conversation_history'].append({
            "role": "user", 
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update mock state to running
        mock_state['status'] = AgentStatus.RUNNING
        emit_status_update()
        
        # Choose different response paths based on the agent mode
        if mock_state['mode'] == AgentMode.AUTO:
            eventlet.spawn(handle_auto_mode_response, text, workflow_name)
        else:
            eventlet.spawn(handle_manual_mode_response, text, workflow_name)
        
    except Exception as e:
        logger.error(f"Error in mock handle_message: {e}", exc_info=True)
        socketio.emit('error', {'message': str(e)})

def handle_auto_mode_response(text, workflow_name):
    """Handle automatic mode responses with multiple tool calls and responses"""
    try:
        # Create a copy of the current request context
        ctx = app.app_context()
        
        def background_task():
            with ctx:
                time.sleep(1)  # Simulate thinking time
                
                # Initial response
                ai_response = create_mock_response_for_input(text, workflow_name)
                socketio.emit('ai_response', {
                    'type': 'ai_response',
                    'content': ai_response,
                })
                
                # Add to mock conversation
                mock_state['conversation_history'].append({
                    "role": "assistant", 
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Create 2-3 tool calls based on the input
                mock_tools = generate_mock_tools_for_input(text, workflow_name)
                
                # Emit tool use group
                socketio.emit('tool_use_group', {
                    'type': 'tool_use_group',
                    'tools': mock_tools
                })
                
                # Emit result for each tool with small delays
                for tool in mock_tools:
                    time.sleep(0.8)  # Simulate tool execution time
                    
                    tool_name = tool['name']
                    tool_result = generate_tool_result(tool)
                    
                    socketio.emit('tool_result', {
                        'type': 'tool_result',
                        'toolUseId': tool['id'],
                        'content': tool_result['content'],
                        'isError': tool_result.get('error') is not None
                    })
                
                time.sleep(1)  # Pause before final response
                
                # Final response after all tool executions
                final_response = create_mock_final_response(text, mock_tools)
                socketio.emit('ai_response', {
                    'type': 'ai_response',
                    'content': final_response,
                })
                
                # Add to mock conversation
                mock_state['conversation_history'].append({
                    "role": "assistant", 
                    "content": final_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update state back to stopped
                mock_state['status'] = AgentStatus.STOPPED
                emit_status_update()
        
        eventlet.spawn(background_task)
        
    except Exception as e:
        logger.error(f"Error in auto mode response: {e}", exc_info=True)
        mock_state['status'] = AgentStatus.STOPPED
        emit_status_update()
        socketio.emit('error', {'message': str(e)})

def handle_manual_mode_response(text, workflow_name):
    """Handle manual mode - just propose actions without executing them"""
    try:
        # Create a copy of the current request context
        ctx = app.app_context()
        
        def background_task():
            with ctx:
                time.sleep(1)  # Simulate thinking time
                
                # Generate response
                ai_response = create_mock_response_for_input(text, workflow_name)
                socketio.emit('ai_response', {
                    'type': 'ai_response',
                    'content': ai_response,
                })
                
                # Add to mock conversation
                mock_state['conversation_history'].append({
                    "role": "assistant", 
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Create 1-2 tool calls but don't execute them
                mock_tools = generate_mock_tools_for_input(text, workflow_name, count=random.randint(1, 2))
                
                # Store in pending tools
                mock_state['pending_tools'] = mock_tools
                
                # Emit tool use group
                socketio.emit('tool_use_group', {
                    'type': 'tool_use_group',
                    'tools': mock_tools
                })
                
                # Update state to stopped but with pending tools
                mock_state['status'] = AgentStatus.STOPPED
                emit_status_update()
        
        eventlet.spawn(background_task)
        
    except Exception as e:
        logger.error(f"Error in manual mode response: {e}", exc_info=True)
        mock_state['status'] = AgentStatus.STOPPED
        emit_status_update()
        socketio.emit('error', {'message': str(e)})

def create_mock_response_for_input(text, workflow_name=None):
    """Create a contextually appropriate mock response based on user input"""
    text_lower = text.lower() if text else ""
    
    if "freecad" in text_lower or mock_state['agent_type'] == 'FreeCAD':
        if "box" in text_lower:
            return "I'll help you create a box in FreeCAD. First, I'll check if FreeCAD is open and then guide you through the process of creating a box with the Part workbench."
        elif "measurement" in text_lower or "dimension" in text_lower:
            return "Let me help you with measurements in FreeCAD. I'll use the measurement tools to determine distances and dimensions of your model."
        else:
            return "I'll help you with your FreeCAD task. Let me first take a screenshot to see what you're working with, and then I'll guide you through the next steps."
    
    elif "openfoam" in text_lower or mock_state['agent_type'] == 'OpenFOAM':
        if "simulation" in text_lower:
            return "I'll help you set up your OpenFOAM simulation. First, let's check your current directory structure and then set up the necessary files."
        elif "mesh" in text_lower:
            return "I'll help you with OpenFOAM mesh generation. We'll need to check your current setup and then create the appropriate mesh based on your requirements."
        else:
            return "I'll assist you with your OpenFOAM task. Let me first check what files we have in the current directory to understand the context better."
    
    # Generic responses for any other case
    elif "create" in text_lower or "make" in text_lower:
        return f"I'll help you create what you need. Let me understand the current state of your system and then guide you through the creation process."
    elif "find" in text_lower or "search" in text_lower:
        return f"I'll help you find what you're looking for. Let me first determine where we need to search and then locate the items you need."
    elif "how" in text_lower:
        return f"I'll explain how to do that. First, I'll check your current setup to provide the most relevant instructions."
    elif workflow_name:
        return f"I'll help you with the '{workflow_name}' workflow. Let me start by understanding your current environment."
    else:
        return f"I'll help you with that request. First, let me take a look at your current state to provide the most relevant assistance."

def create_mock_final_response(text, tools):
    """Create a mock final response that references the tools used"""
    tool_names = [tool['name'] for tool in tools]
    
    if 'computer' in tool_names and 'bash' in tool_names:
        return "I've analyzed your screen and executed the necessary commands. Based on what I found, you can proceed with the next steps in your task. Let me know if you need further assistance."
    
    elif 'computer' in tool_names:
        return "I've analyzed your screen and identified the key elements. I can see the main interface and the relevant components needed for your task. Let me know what specific aspect you'd like me to help with next."
    
    elif 'bash' in tool_names:
        return "I've executed the necessary commands and analyzed the output. The system is properly configured for your task. You can now proceed with the next steps or let me know if you need additional help."
    
    elif 'file' in tool_names:
        return "I've examined the file contents and structure. The files are organized as expected, and I can see the relevant data needed for your task. Let me know what you'd like to do next with this information."
    
    else:
        return "I've completed the requested operations. Everything is set up as needed for your task. Feel free to ask if you need any clarification or additional assistance."

def generate_mock_tools_for_input(text, workflow_name=None, count=None):
    """Generate appropriate mock tools based on user input and context"""
    if count is None:
        count = random.randint(2, 3)
    
    tools = []
    text_lower = text.lower() if text else ""
    
    # Always start with a screenshot for context if dealing with GUI apps
    if mock_state['agent_type'] in ['FreeCAD', 'CAD']:
        tools.append({
            'id': f'tool_call_{uuid.uuid4().hex[:8]}',
            'name': 'computer',
            'input': {'action': 'screenshot'}
        })
        count -= 1
    
    # Add file operations for workflow-related tasks
    if workflow_name or 'file' in text_lower or 'open' in text_lower:
        if count > 0:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'file',
                'input': {'action': 'list', 'path': './'}
            })
            count -= 1
    
    # Add bash commands for various scenarios
    if count > 0 and ('command' in text_lower or 'run' in text_lower or 'bash' in text_lower or 'terminal' in text_lower):
        if 'freecad' in text_lower:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'bash',
                'input': {'command': 'which freecad || locate freecad'}
            })
        elif 'openfoam' in text_lower:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'bash',
                'input': {'command': 'ls -la && echo $WM_PROJECT_DIR'}
            })
        else:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'bash',
                'input': {'command': 'ls -la && pwd'}
            })
        count -= 1
    
    # Add additional tools if needed
    while count > 0:
        if "click" in text_lower or "button" in text_lower:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'computer',
                'input': {'action': 'click', 'x': random.randint(100, 800), 'y': random.randint(100, 600)}
            })
        elif "type" in text_lower or "text" in text_lower:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'computer',
                'input': {'action': 'type', 'text': 'example input text'}
            })
        elif "read" in text_lower or "content" in text_lower:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'file',
                'input': {'action': 'read', 'path': 'example.txt'}
            })
        elif "find" in text_lower or "search" in text_lower:
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'bash',
                'input': {'command': 'find . -name "*.py" | grep -i example'}
            })
        else:
            # Default to checking system info
            tools.append({
                'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                'name': 'bash',
                'input': {'command': 'uname -a && df -h'}
            })
        count -= 1
    
    return tools

def generate_tool_result(tool):
    """Generate appropriate mock result for a given tool call"""
    tool_name = tool['name']
    tool_input = tool['input']
    
    if tool_name == 'computer':
        action = tool_input.get('action')
        if action in MOCK_TOOL_RESPONSES['computer']:
            return MOCK_TOOL_RESPONSES['computer'][action]
        return {'content': f"Mock result for computer action: {action}", 'error': None}
    
    elif tool_name == 'bash':
        command = tool_input.get('command', '').strip()
        
        # Try to match the command with specific mock responses
        if command.startswith('ls'):
            return MOCK_TOOL_RESPONSES['bash']['ls']
        elif command.startswith('pwd'):
            return MOCK_TOOL_RESPONSES['bash']['pwd']
        elif command.startswith('cat'):
            return MOCK_TOOL_RESPONSES['bash']['cat']
        elif command.startswith('invalid'):  # Demonstrate error handling
            return MOCK_TOOL_RESPONSES['bash']['error_example']
        
        # Default bash response
        return MOCK_TOOL_RESPONSES['bash']['default']
    
    elif tool_name == 'file':
        action = tool_input.get('action')
        if action in MOCK_TOOL_RESPONSES['file']:
            return MOCK_TOOL_RESPONSES['file'][action]
        return MOCK_TOOL_RESPONSES['file']['default']
    
    # Default case
    return {'content': f"Mock result for {tool_name} operation", 'error': None}

@socketio.on('control_update')
def handle_control_update(data):
    logger.info(f'Mock control update received: {data}')
    try:
        # Update the mock state
        if 'agentType' in data:
            mock_state['agent_type'] = data['agentType']
        if 'mode' in data:
            new_mode = data['mode']
            if new_mode in [mode.value for mode in AgentMode]:
                mock_state['mode'] = AgentMode(new_mode)
        
        # Emit the updated state
        emit_status_update()
    except Exception as e:
        logger.error(f"Error in mock handle_control_update: {e}", exc_info=True)
        socketio.emit('error', {'message': str(e)})

@socketio.on('execute_next_tool')
def handle_execute_next_tool():
    logger.info('Received mock execute_next_tool request')
    try:
        # Check if there are pending tools
        if not mock_state['pending_tools']:
            logger.info("No pending tools to execute")
            socketio.emit('warning', {'message': 'No pending tools to execute'})
            return
        
        # Create a copy of the current request context
        ctx = app.app_context()
        
        def background_task():
            with ctx:
                # Take the first pending tool
                tool = mock_state['pending_tools'].pop(0)
                
                # Update state to running
                mock_state['status'] = AgentStatus.RUNNING
                emit_status_update()
                
                time.sleep(1)  # Simulate processing time
                
                # Generate and emit result
                result = generate_tool_result(tool)
                socketio.emit('tool_result', {
                    'type': 'tool_result',
                    'toolUseId': tool['id'],
                    'content': result['content'],
                    'isError': result.get('error') is not None
                })
                
                # Update state back to stopped
                mock_state['status'] = AgentStatus.STOPPED
                emit_status_update()
        
        eventlet.spawn(background_task)
    except Exception as e:
        logger.error(f"Error in mock execute_next_tool: {e}", exc_info=True)
        socketio.emit('error', {'message': str(e)})

@socketio.on('generate_next_action')
def handle_generate_next_action():
    logger.info('Received mock generate_next_action request')
    try:
        # Create a copy of the current request context
        ctx = app.app_context()
        
        def background_task():
            with ctx:
                # Update state to running
                mock_state['status'] = AgentStatus.RUNNING
                emit_status_update()
                
                time.sleep(1.5)  # Simulate thinking time
                
                # Get last message for context
                last_message = mock_state['conversation_history'][-1]['content'] if mock_state['conversation_history'] else "previous context"
                
                # Generate mock response
                ai_response = f"Based on our previous conversation about {last_message[:30]}..., I suggest we proceed with the following action:"
                socketio.emit('ai_response', {
                    'type': 'ai_response',
                    'content': ai_response,
                })
                
                # Add to mock conversation
                mock_state['conversation_history'].append({
                    "role": "assistant", 
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Generate a new mock tool
                mock_tool = {
                    'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                    'name': random.choice(['computer', 'bash', 'file']),
                    'input': {'action': 'click', 'x': 150, 'y': 250} if random.choice([True, False]) else {'command': 'ls -la'}
                }
                
                # Store in pending tools
                mock_state['pending_tools'] = [mock_tool]
                
                # Emit tool use group
                socketio.emit('tool_use_group', {
                    'type': 'tool_use_group',
                    'tools': [mock_tool]
                })
                
                # Update state back to stopped
                mock_state['status'] = AgentStatus.STOPPED
                emit_status_update()
        
        eventlet.spawn(background_task)
    except Exception as e:
        logger.error(f"Error in mock generate_next_action: {e}", exc_info=True)
        socketio.emit('error', {'message': str(e)})

@socketio.on('execute_tool_and_generate_action')
def handle_execute_tool_and_generate_action():
    logger.info('Received mock execute_tool_and_generate_action request')
    try:
        # Create a copy of the current request context
        ctx = app.app_context()
        
        def background_task():
            with ctx:
                # Update state to running
                mock_state['status'] = AgentStatus.RUNNING
                emit_status_update()
                
                # Check if there are pending tools
                if not mock_state['pending_tools']:
                    logger.info("No pending tools to execute in combined operation")
                    # Still proceed with generating new action
                else:
                    # Take the first pending tool and execute it
                    tool = mock_state['pending_tools'].pop(0)
                    
                    time.sleep(1)  # Simulate processing time
                    
                    # Generate and emit tool result
                    result = generate_tool_result(tool)
                    socketio.emit('tool_result', {
                        'type': 'tool_result',
                        'toolUseId': tool['id'],
                        'content': result['content'],
                        'isError': result.get('error') is not None
                    })
                
                time.sleep(1)  # Pause between operations
                
                # Generate mock response
                ai_response = "Based on the tool execution and our context, I suggest we take the following action:"
                socketio.emit('ai_response', {
                    'type': 'ai_response',
                    'content': ai_response,
                })
                
                # Add to mock conversation
                mock_state['conversation_history'].append({
                    "role": "assistant", 
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Generate a new mock tool
                mock_tool = {
                    'id': f'tool_call_{uuid.uuid4().hex[:8]}',
                    'name': 'bash',
                    'input': {'command': 'grep -r "important_pattern" ./src'}
                }
                
                # Update pending tools
                mock_state['pending_tools'] = [mock_tool]
                
                # Emit tool use group
                socketio.emit('tool_use_group', {
                    'type': 'tool_use_group',
                    'tools': [mock_tool]
                })
                
                # Update state back to stopped
                mock_state['status'] = AgentStatus.STOPPED
                emit_status_update()
        
        eventlet.spawn(background_task)
    except Exception as e:
        logger.error(f"Error in mock combined operation: {e}", exc_info=True)
        socketio.emit('error', {'message': str(e)})

# Minimal implementation of training endpoints - just return mock data

@socketio.on('upload_screenshot')
def handle_screenshot_upload(data):
    try:
        # Minimal mock response - we're not implementing training agent details
        mock_result = {
            'image_id': f'mock_image_{uuid.uuid4().hex[:8]}',
            'status': 'success',
            'message': 'Screenshot uploaded but not processed (training agent functionality not mocked)'
        }
        
        emit('detection_result', mock_result)
    except Exception as e:
        logger.error(f"Error in mock screenshot processing: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('save_templates')
def handle_save_templates(data):
    try:
        # Minimal mock response
        emit('templates_saved', {
            'success': True, 
            'message': 'Templates would be saved here (training agent functionality not mocked)'
        })
    except Exception as e:
        logger.error(f"Error in mock template saving: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('ping')
def handle_ping():
    emit('pong')

@socketio.on('new_chat')
def handle_new_chat(data):
    logger.info('Starting new mock chat')
    try:
        # Update mock state with new agent type
        agent_name = data.get('agent_name', 'FreeCAD')
        mock_state['agent_type'] = agent_name
        
        # Reset conversation history but use pre-seeded conversation if available
        if agent_name in MOCK_CONVERSATIONS:
            mock_state['conversation_history'] = MOCK_CONVERSATIONS[agent_name].copy()
        else:
            mock_state['conversation_history'] = [
                {"role": "system", "content": f"You are an AI assistant for {agent_name}."}
            ]
        
        # Reset pending tools
        mock_state['pending_tools'] = []
        
        emit('chat_reset', {'status': 'success'})
        emit_status_update()
    except Exception as e:
        logger.error(f"Error in mock new chat: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('get_screenshots')
def handle_get_screenshots(data):
    try:
        # Minimal mock implementation
        mock_screenshots = [
            {'id': f'mock_screenshot_{i}', 
             'timestamp': datetime.now().isoformat(),
             'name': f'Mock Screenshot {i}'} 
            for i in range(1, 4)
        ]
        
        emit('screenshots_list', {'screenshots': mock_screenshots})
    except Exception as e:
        logger.error(f"Error in mock get_screenshots: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('get_workflows')
def handle_get_workflows():
    logger.info('🔍 Received mock get_workflows request')
    try:
        # Workflow names based on agent type
        if mock_state['agent_type'] == 'FreeCAD':
            mock_workflows = [
                'CAD Basic Design',
                'CAD Advanced Modeling',
                'Part Design Workflow',
                'Technical Drawing',
                'Assembly Design'
            ]
        elif mock_state['agent_type'] == 'OpenFOAM':
            mock_workflows = [
                'CFD Simulation Setup',
                'Mesh Generation',
                'Post-processing',
                'Parameter Study',
                'Results Analysis'
            ]
        else:
            mock_workflows = [
                'Basic Workflow',
                'Advanced Analysis',
                'Documentation',
                'Debugging',
                'Project Setup'
            ]
        
        logger.info(f'📋 Retrieved mock workflows: {mock_workflows}')
        emit('workflows_list', {'workflows': mock_workflows})
        logger.info('✅ Successfully sent mock workflows_list event')
    except Exception as e:
        logger.error(f"❌ Error in mock get_workflows: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('get_agents')
def handle_get_agents():
    logger.info('🔍 Received mock get_agents request')
    try:
        # Standard list of mock agents
        mock_agents = ['FreeCAD', 'OpenFOAM', 'Generic', 'CAD', 'DataAnalysis']
        
        logger.info(f'📋 Retrieved mock agents: {mock_agents}')
        emit('agents_list', {'agents': mock_agents})
        logger.info('✅ Successfully sent mock agents_list event')
    except Exception as e:
        logger.error(f"❌ Error in mock get_agents: {e}", exc_info=True)
        emit('error', {'message': str(e)})

# Error handling for socket events
@socketio.on_error()
def error_handler(e):
    logger.error(f"Mock SocketIO error: {str(e)}")
    emit('error', {'message': str(e)})

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Mock SocketIO default error: {str(e)}")
    emit('error', {'message': str(e)})

# Add REST API endpoints for health check and info
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'version': '1.0.0-mock'})

@app.route('/info')
def server_info():
    return jsonify({
        'name': 'Mock Compass Backend',
        'version': '1.0.0-mock',
        'agents': ['FreeCAD', 'OpenFOAM', 'Generic', 'CAD', 'DataAnalysis'],
        'mode': mock_state['mode'],
        'status': mock_state['status']
    })

if __name__ == '__main__':
    try:
        print("Starting mock Compass backend server on port 5001...")
        print("This is a MOCK server - no actual LLM or tool execution will happen")
        print("Available mock agents: FreeCAD, OpenFOAM, Generic, CAD, DataAnalysis")
        socketio.run(app, 
            host='0.0.0.0',
            debug=True, 
            port=5001,
            use_reloader=False,
            log_output=True)
    except KeyboardInterrupt:
        cleanup() 