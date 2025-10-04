import asyncio
import logging
import os
import sys
import tempfile
import traceback
from io import StringIO
from typing import Literal, Dict, Any, Optional, List, Union
import comtypes.client

helper = comtypes.client.CreateObject('SAP2000v1.Helper')
from anthropic.types.beta import BetaToolUnionParam
from compass.tools.base import BaseTool
from compass.types.agent import ToolResult
from compass.tools.sap2000.sap_model_info import SAPModelInfo
from compass.tools.sap2000.sap_api_query import SAPAPIQuery
from compass.tools.sap2000.core import CustomSAP2000Model
from compass.tools.sap2000.core.config_manager import ModelConfig

logger = logging.getLogger(__name__)

class SAPComTool(BaseTool):
    """Tool for interacting with SAP2000 via COM interface."""
    name: Literal["sap_com"] = "sap_com"
    
    def __init__(self):
        """Initialize the SAP2000 COM tool without connecting immediately."""
        self.sap_object = None
        self.sap_model = None
        self.model_path = None
        self._connected = False
        self.model_info = None
        self.execution_state = {}  # Dictionary to maintain state between executions
        self._connection_status = "DISCONNECTED"  # New field to track connection status
        self.config = None
        
        # Initialize API query system for documentation searches
        try:
            self.api_query = SAPAPIQuery()
            logger.info("Initialized SAP API Query system")
        except Exception as e:
            logger.error(f"Error initializing API query system: {str(e)}")
            self.api_query = None
        
        # No longer attempting connection on init
        logger.info("SAP2000 tool initialized in lightweight mode (not connected)")

    def _load_config(self, config_path=None):
        """Load the configuration file from the specified path or default location"""
        try:
            # If config_path is provided, use it, otherwise determine from environment
            if not config_path:
                # Get project root from workspace folder environment variable
                project_root = os.getenv('WORKSPACE_FOLDER')
                if not project_root:
                    # Fallback to current working directory if env var not set
                    project_root = os.getcwd()
                
                config_path = os.path.join(project_root, 'backend', 'src', 'compass', 'config', 'sap_project', 'config.yaml')
            
            self.config = ModelConfig.from_yaml(config_path)
            logger.info(f"Successfully loaded configuration from {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return False
    
    def _try_connect(self) -> bool:
        try:
            logger.info("Attempting to connect to SAP2000...")
            self._connection_status = "CONNECTING"
            helper = comtypes.client.CreateObject('SAP2000v1.Helper')
            helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper) #type: ignore
            self.sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
            # Wrap the SAP model in our custom class
            import comtypes.gen.SAP2000v1 as SAP2000
            
            # Store raw SAP model first
            raw_sap_model = self.sap_object.SapModel
            
            # Always create CustomSAP2000Model, with or without config
            self.sap_model = CustomSAP2000Model(raw_sap_model, self.config)
                
            if self.sap_model is None:
                self._connection_status = "DISCONNECTED"
                raise Exception("Failed to connect to SAP2000.")
            
            # Get program info from the custom model (it forwards to the raw model)
            info = self.sap_model.GetProgramInfo()
                
            logger.info(f"Successfully connected to SAP2000 (Version: {info[0]}, Build: {info[1]})")
            self._connected = True
            self._connection_status = "CONNECTED"
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SAP2000: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connected = False
            self._connection_status = "DISCONNECTED"
            return False
    
    # New method to explicitly connect to SAP
    async def connect_to_sap(self) -> ToolResult:
        """Explicitly connect to SAP2000."""
        if self._connected:
            return ToolResult(text="Already connected to SAP2000")
        
        success = self._try_connect()
        if success:
            return ToolResult(text="Successfully connected to SAP2000")
        else:
            return ToolResult(error="Failed to connect to SAP2000. Make sure SAP2000 is running.")
    
    # New method to explicitly load configuration
    async def load_sap_config(self, config_path=None) -> ToolResult:
        """Explicitly load SAP2000 configuration."""
        if self._load_config(config_path):
            # If we have an existing CustomSAP2000Model, update its config
            if self.sap_model and hasattr(self.sap_model, 'update_config') and self.config is not None:
                self.sap_model.update_config(self.config)
            return ToolResult(text="Successfully loaded SAP2000 configuration")
        else:
            return ToolResult(error="Failed to load SAP2000 configuration")
    
    # New method to get connection status
    def get_connection_status(self) -> str:
        """Get the current connection status."""
        return self._connection_status
    
    def _generate_unique_path(self, base_path: str, base_filename: str) -> str:
        """Generate a unique path by adding suffix if file exists."""
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        
        path = os.path.join(base_path, base_filename)
        if not os.path.exists(path):
            return path
        
        # If file exists, add suffix
        name, ext = os.path.splitext(base_filename)
        counter = 1
        while True:
            new_path = os.path.join(base_path, f"{name}_{counter}{ext}")
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    async def __call__(
        self,
        *,
        action: Literal["run_sap_com_python", "get_model_info", "query_api_info"],
        script_command: Optional[str] = None,
        query: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Execute SAP2000 related actions based on the specified action type.
        
        Args:
            action: The type of action to perform
            script_command: Python script to execute (for run_sap_com_python action)
            query: List of queries to search in the SAP2000 API documentation (for query_api_info action)
            
        Returns:
            ToolResult containing execution results or error
        """
        # If not connected, try to connect (for actions that require SAP2000)
        if action in ["run_sap_com_python", "get_model_info"] and not self._connected:
            return ToolResult(
                error="Not connected to SAP2000. Make sure SAP2000 is running with a model open and connect using the SAP connection button."
            )
        
        # Handle the requested action
        if action == "run_sap_com_python":
            if not script_command:
                return ToolResult(
                    error="script_command parameter is required for run_sap_com_python action"
                )
            return await self._execute_python_script(script_command)
        
        elif action == "get_model_info":
            return await self._get_model_info()
        
        elif action == "query_api_info":
            if not query:
                return ToolResult(
                    error="query parameter is required for query_api_info action"
                )
            return await self._query_api_info(query)
        
        else:
            return ToolResult(
                error=f"Unknown action: {action}"
            )
    
    async def _execute_python_script(self, script: str) -> ToolResult:
        """Execute a Python script with access to the SAP2000 API."""
        try:
            # Capture stdout and stderr
            stdout_buffer = StringIO()
            stderr_buffer = StringIO()
            original_stdout, original_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = stdout_buffer, stderr_buffer
            
            # Make sap_object and sap_model available to the executed script
            sap_object = self.sap_object
            sap_model = self.sap_model
            
            # Set up a dictionary of variables to pass to exec, including our execution state
            exec_globals = {
                'sap_object': sap_object,
                'sap_model': sap_model,
                'sys': sys,
                'traceback': traceback,
                'os': os,
                'StringIO': StringIO,
                'ModelPath': self.model_path,
                **self.execution_state  # Include our persistent state
            }
            
            try:
                # Execute the user script with access to the SAP objects
                exec(script, exec_globals)
                
                # Update our execution state with any new variables
                self.execution_state.update({
                    k: v for k, v in exec_globals.items() 
                    if k not in ['sap_object', 'sap_model', 'sys', 'traceback', 'os', 'StringIO', 'ModelPath']
                })
                
                # Automatically refresh the view and save the model after script execution
                try:
                    ret = self.sap_model.View.RefreshView(0, False) #type: ignore
                    if ret != 0:
                        error_text = f"\nFailed to refresh view (return code: {ret})"
                    else:
                        error_text = ""
                    
                    ret = self.sap_model.File.Save(self.model_path) #type: ignore
                    if ret != 0:
                        error_text += f"\nFailed to save model (return code: {ret})"
                except Exception as e:
                    logger.warning(f"Error during automatic view refresh and save: {str(e)}")
                
                result_text = stdout_buffer.getvalue()
                error_text = stderr_buffer.getvalue()
            except Exception as e:
                # Get the traceback
                tb = traceback.extract_tb(e.__traceback__)
                
                # Filter out frames from our codebase and comtypes
                filtered_tb = []
                for frame in tb:
                    # Skip frames from our codebase and comtypes
                    if not any(x in frame.filename for x in ['compass/tools/sap2000', 'comtypes']):
                        filtered_tb.append(frame)
                
                # Create a new traceback with just the filtered frames
                if filtered_tb:
                    # Create a new exception with the filtered traceback
                    new_exc = type(e)(str(e))
                    # Use a simpler approach to report traceback instead of trying to create one
                    error_text = f"Error in script: {str(new_exc)}\n{''.join(traceback.format_list(filtered_tb))}"
                else:
                    error_text = f"Error in script: {str(e)}"
                
                result_text = stdout_buffer.getvalue()  # Capture any output before the error
            finally:
                # Restore stdout and stderr
                sys.stdout, sys.stderr = original_stdout, original_stderr
            
            # Handle error case
            if error_text:
                return ToolResult(
                    text=result_text,
                    error=error_text
                )
            
            # Return successful result
            return ToolResult(
                text=result_text,
                system="Executed SAP2000 script successfully"
            )
        except Exception as e:
            # Catch any unexpected errors in our handling code
            return ToolResult(error=f"Error executing script: {str(e)}")
    
    async def _get_model_info(self) -> ToolResult:
        """Extract and return comprehensive information about the current SAP2000 model."""
        try:
            # Check if we have a valid model_info
            if not self.model_info:
                return ToolResult(
                    error="No valid SAP2000 model available. Make sure SAP2000 is running with a model open."
                )
                
            # Save the model first to ensure all information is up to date
            save_result = self.model_info.save_model()
            logger.info(f"Save model result: {save_result}")
            
            # Extract and format model information
            model_info_text = self.model_info.format_model_info()
            
            return ToolResult(
                text=model_info_text,
                system="SAP2000 model information extracted successfully"
            )
        except Exception as e:
            return ToolResult(
                error=f"Error extracting model information: {str(e)}\n{traceback.format_exc()}"
            )
    
    async def _query_api_info(self, queries: List[str]) -> ToolResult:
        """
        Query the SAP2000 API documentation for information.
        
        Args:
            queries: List of query strings to search in the API documentation
            
        Returns:
            ToolResult containing query results or error
        """
        try:
            # Check if API query system is initialized
            if self.api_query is None:
                return ToolResult(
                    error="API query system is not initialized. Please check the logs for initialization errors."
                )
            
            # Execute the queries
            query_results = self.api_query.query_api_docs(queries)
            
            # Format the results
            formatted_results = self.api_query.format_api_query_results(query_results)
            
            return ToolResult(
                text=formatted_results,
                system="SAP2000 API documentation query completed successfully"
            )
            
        except Exception as e:
            return ToolResult(
                error=f"Error querying API documentation: {str(e)}\n{traceback.format_exc()}"
            )
    
    def to_params(self) -> BetaToolUnionParam:
        """Return the parameters needed to register this tool with the LLM."""
        return {
            "name": self.name,
            "description": """Tool for interacting with SAP2000 structural analysis software via its COM API.
Supports following main actions:
1. run_sap_com_python: Execute Python scripts to interact with a running SAP2000 instance

The connection to SAP2000 is established when the agent starts.
For run_sap_com_python, the script is given direct access to the SAP2000 model via the 'sap_model' variable.
In addition, the following variables are available:
- sap_model: The SAP2000 model object
- sap_object: The SAP2000 object
- os: The os module
- ModelPath: The path to the model file
Also after running the script, the model will be automatically saved and view will be refreshed (you don't need to do it manually).

Important notes when using run_sap_com_python:
- Always try to return the "ret" value of commands in the script and print it to check if successful.
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["run_sap_com_python"],
                        "description": "The type of SAP2000 interaction to perform"
                    },
                    "script_command": {
                        "type": "string",
                        "description": "The Python script to execute with access to SAP2000 API (required for run_sap_com_python action)"
                    }
                },
                "required": ["action"]
            },
            "cache_control": {"type": "ephemeral"}
        } # type: ignore

    def to_params_all(self) -> BetaToolUnionParam:
        """Return the parameters needed to register this tool with the LLM."""
        return {
            "name": self.name,
            "description": """Tool for interacting with SAP2000 structural analysis software via its COM API.
Supports three main actions:
1. run_sap_com_python: Execute Python scripts to interact with a running SAP2000 instance
2. get_model_info: Extract comprehensive information about the current SAP2000 model
3. query_api_info: Query information about the SAP2000 API (documentation search)

The connection to SAP2000 is established when the agent starts.
For run_sap_com_python, the script is given direct access to the SAP2000 model via the 'sap_model' variable.
In addition, the following variables are available:
- sap_model: The SAP2000 model object
- sap_object: The SAP2000 object
- os: The os module
- ModelPath: The path to the model file
Also after running the script, the model will be automatically saved and view will be refreshed (you don't need to do it manually).

Important notes when using run_sap_com_python:
- Always try to return the "ret" value of commands in the script and print it to check if successful.
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["run_sap_com_python", "get_model_info", "query_api_info"],
                        "description": "The type of SAP2000 interaction to perform"
                    },
                    "script_command": {
                        "type": "string",
                        "description": "The Python script to execute with access to SAP2000 API (required for run_sap_com_python action)"
                    },
                    "query": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of queries to search in the SAP2000 API documentation (required for query_api_info action)"
                    }
                },
                "required": ["action"]
            },
            "cache_control": {"type": "ephemeral"}
        } # type: ignore  