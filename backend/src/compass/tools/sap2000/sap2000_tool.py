import logging
import asyncio
import tempfile
import os
import sys
import traceback
from io import StringIO
from typing import Literal, Dict, Any, Optional, List, Union

from anthropic.types.beta import BetaToolUnionParam
from compass.tools.base import BaseTool
from compass.types.agent import ToolResult
from compass.tools.sap2000.sap_model_info import SAPModelInfo
from compass.tools.sap2000.sap_api_query import SAPAPIQuery

logger = logging.getLogger(__name__)

class SAPComTool(BaseTool):
    """Tool for interacting with SAP2000 via COM interface."""
    name: Literal["sap_com"] = "sap_com"
    
    def __init__(self):
        """Initialize the SAP2000 COM tool and try to connect to a running instance."""
        self.sap_object = None
        self.sap_model = None
        self.model_path = None
        self._connected = False
        self.model_info = None
        
        # Initialize API query system for documentation searches
        try:
            self.api_query = SAPAPIQuery()
            logger.info("Initialized SAP API Query system")
        except Exception as e:
            logger.error(f"Error initializing API query system: {str(e)}")
            self.api_query = None
        
        # Try to connect immediately upon initialization
        self._try_connect()
    
    def _try_connect(self):
        """Attempt to connect to a running SAP2000 instance."""
        try:
            import comtypes.client
            import comtypes.gen.SAP2000v1
            logger.info("Attempting to connect to SAP2000...")
            helper = comtypes.client.CreateObject('SAP2000v1.Helper')
            helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
            self.sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
            self.sap_model = self.sap_object.SapModel
            APIPath = R'C:\Users\sadoughi\Projects\compass\experiment\model'
            self.model_path = APIPath + os.sep + 'compass_model.sdb'
            
            # Initialize model info extractor
            self.model_info = SAPModelInfo(self.sap_model, self.sap_object, self.model_path)
            
            # Test if the connection is valid by getting program info
            info = self.sap_model.GetProgramInfo()
            
            logger.info(f"Successfully connected to SAP2000 (Version: {info[0]}, Build: {info[1]})")
            self._connected = True
            return True
        except ImportError:
            logger.error("Failed to import comtypes. Make sure it's installed: pip install comtypes")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Failed to connect to SAP2000: {str(e)}")
            self._connected = False
            return False
    
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
            if not self._try_connect():
                return ToolResult(
                    error="Not connected to SAP2000. Make sure SAP2000 is running with a model open."
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
            
            # Set up a dictionary of variables to pass to exec
            exec_globals = {
                'sap_object': sap_object,
                'sap_model': sap_model,
                'sys': sys,
                'traceback': traceback,
                'os': os,
                'StringIO': StringIO,
                'ModelPath': self.model_path
            }
            
            try:
                # Execute the user script with access to the SAP objects
                exec(script, exec_globals)
                result_text = stdout_buffer.getvalue()
                error_text = stderr_buffer.getvalue()
            except Exception as e:
                error_text = f"Error executing script: {str(e)}\n{traceback.format_exc()}"
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

Therefore, you can assume these variables are available and rely on them. 
Important notes when using run_sap_com_python:
- Always save the model before running any analysis. Otherwise, the analysis won't be performed. Use:
  ret = sap_model.File.Save(ModelPath)
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
            }
        } # type: ignore 