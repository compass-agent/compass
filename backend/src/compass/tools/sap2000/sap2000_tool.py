import logging
import asyncio
import tempfile
import os
import sys
import traceback
from io import StringIO
from typing import Literal, Dict, Any, Optional

from anthropic.types.beta import BetaToolUnionParam
from compass.tools.base import BaseTool
from compass.types.agent import ToolResult

logger = logging.getLogger(__name__)

class SAPComTool(BaseTool):
    """Tool for interacting with SAP2000 via COM interface."""
    name: Literal["sap_com"] = "sap_com"
    
    def __init__(self):
        """Initialize the SAP2000 COM tool and try to connect to a running instance."""
        self.sap_object = None
        self.sap_model = None
        self._connected = False
        
        # Try to connect immediately upon initialization
        self._try_connect()
    
    def _try_connect(self):
        """Attempt to connect to a running SAP2000 instance."""
        try:
            import comtypes.client
            
            logger.info("Attempting to connect to SAP2000...")
            
            # Using Helper object to connect to SAP2000
            helper = comtypes.client.CreateObject("SAP2000v1.Helper")
            helper.CreateObject("SAP2000.SapObject")
            self.sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
            self.sap_model = self.sap_object.SapModel
            
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
        script: str
    ) -> ToolResult:
        """
        Execute the given Python script with direct access to the SAP2000 model.
        
        Args:
            script: Python script to execute
            
        Returns:
            ToolResult containing execution results or error
        """
        # If not connected, try to connect
        if not self._connected:
            if not self._try_connect():
                return ToolResult(
                    error="Not connected to SAP2000. Make sure SAP2000 is running with a model open."
                )
        
        # Execute the script directly in the current process
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
                'StringIO': StringIO
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
    
    def to_params(self) -> BetaToolUnionParam:
        """Return the parameters needed to register this tool with the LLM."""
        return {
            "name": self.name,
            "description": """Execute Python scripts to interact with a running SAP2000 instance via its COM API.
The connection to SAP2000 is established when the agent starts, so you don't need to check the connection.
The script is given direct access to the SAP2000 model via the 'sap_model' variable.

Example format for scripts:
```python
# Create a new model
ret = sap_model.File.NewBlank()

# Define units (kip, in)
ret = sap_model.SetPresentUnits(6)  

# Add a point at coordinates (0,0,0)
ret = sap_model.PointObj.AddCartesian(0, 0, 0, "P1")

# Get information about the model
info = sap_model.GetProgramInfo()
print(f"SAP2000 Version: {info[0]}")
```
Always capture return values with 'ret = ' and include proper error handling.
Always format code with proper indentation and helpful comments.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "The Python script to execute with access to SAP2000 API (via sap_model variable). Format properly with indentation and comments."
                    }
                },
                "required": ["script"]
            }
        } # type: ignore 