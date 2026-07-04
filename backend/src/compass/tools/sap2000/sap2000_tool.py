import asyncio
import csv
import logging
import os
import subprocess
import sys
import tempfile
import traceback
from io import StringIO
from typing import Any, Dict, List, Literal, Optional, Union

import comtypes.client
from anthropic.types.beta import BetaToolUnionParam
from compass.runtime_paths import IS_FROZEN, get_bundle_dir, get_workspace_dir
from compass.tools.base import BaseTool
from compass.tools.sap2000.core import CustomSAP2000Model
from compass.tools.sap2000.core.config_manager import ModelConfig
from compass.tools.sap2000.sap_api_query import SAPAPIQuery
from compass.tools.sap2000.sap_model_info import SAPModelInfo
from compass.types.agent import ToolResult

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
        self._last_connect_error = None
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
            # If config_path is provided, use it, otherwise use the bundled default
            if not config_path:
                if IS_FROZEN:
                    config_path = str(get_bundle_dir() / 'compass' / 'config' / 'sap_project' / 'config.yaml')
                else:
                    project_root = str(get_workspace_dir())
                    config_path = os.path.join(project_root, 'backend', 'src', 'compass', 'config', 'sap_project', 'config.yaml')
            
            self.config = ModelConfig.from_yaml(config_path)
            logger.info(f"Successfully loaded configuration from {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return False

    def _resolve_model_path(self) -> str:
        """Return a stable save path for the current SAP2000 model."""
        try:
            current_file = self.sap_model.GetModelFilename() if self.sap_model else None # type: ignore
            if current_file:
                return current_file
        except Exception:
            pass

        configured_dir = None
        try:
            if self.config and self.config.general:
                configured_dir = self.config.general.get('model_path')
        except Exception:
            configured_dir = None

        if configured_dir:
            model_dir = os.path.expanduser(str(configured_dir))
            if not os.path.isabs(model_dir):
                model_dir = os.path.join(str(get_workspace_dir()), model_dir)
        else:
            model_dir = os.path.join(str(get_workspace_dir()), 'models')

        return self._generate_unique_path(model_dir, 'compass_model.sdb')

    def _refresh_model_context(self) -> None:
        """Refresh helper state derived from the current SAP2000 model."""
        if not self.sap_model:
            self.model_path = None
            self.model_info = None
            return

        self.model_path = self._resolve_model_path()
        self.model_info = SAPModelInfo(self.sap_model, self.sap_object, self.model_path)
        logger.info(f"SAP2000 model path set to {self.model_path}")
    
    @staticmethod
    def _get_sap2000_process_ids() -> Optional[List[int]]:
        """Best-effort list of running SAP2000.exe process IDs."""
        try:
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq SAP2000.exe', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=15,
                creationflags=creationflags,
            )
            process_ids = []
            for row in csv.reader(StringIO(result.stdout or '')):
                if len(row) >= 2 and row[0].lower() == 'sap2000.exe':
                    try:
                        process_ids.append(int(row[1]))
                    except ValueError:
                        pass
            return process_ids
        except Exception as e:
            logger.warning(f"Could not check for SAP2000 process: {e}")
            return None

    @staticmethod
    def _is_sap2000_process_running() -> Optional[bool]:
        """Best-effort check whether a SAP2000.exe process exists.

        Returns True/False, or None if the check itself failed.
        """
        process_ids = SAPComTool._get_sap2000_process_ids()
        if process_ids is None:
            return None
        return bool(process_ids)

    @staticmethod
    def _is_process_elevated(process_id: Optional[int] = None) -> Optional[bool]:
        """Whether a process runs elevated (as Administrator). None if unknown.

        With no process_id, checks the current process. Windows COM isolates
        elevated from non-elevated processes, so a mismatch between Compass
        and SAP2000 makes the COM attach silently fail.
        """
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            advapi32 = ctypes.windll.advapi32

            if process_id is None:
                process_handle = kernel32.GetCurrentProcess()
                opened = False
            else:
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                process_handle = kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION, False, int(process_id))
                if not process_handle:
                    return None
                opened = True

            try:
                TOKEN_QUERY = 0x0008
                token = wintypes.HANDLE()
                if not advapi32.OpenProcessToken(
                        process_handle, TOKEN_QUERY, ctypes.byref(token)):
                    return None
                try:
                    TokenElevation = 20
                    elevation = wintypes.DWORD()
                    returned = wintypes.DWORD()
                    if not advapi32.GetTokenInformation(
                            token, TokenElevation, ctypes.byref(elevation),
                            ctypes.sizeof(elevation), ctypes.byref(returned)):
                        return None
                    return bool(elevation.value)
                finally:
                    kernel32.CloseHandle(token)
            finally:
                if opened:
                    kernel32.CloseHandle(process_handle)
        except Exception:
            return None

    @classmethod
    def _get_sap2000_modal_dialog(cls) -> Optional[str]:
        """Title of a visible dialog (#32770) owned by SAP2000, if any.

        While such a dialog is open, SAP2000's COM interface blocks and any
        API call will hang until the user answers it.
        """
        process_ids = cls._get_sap2000_process_ids() or []
        if not process_ids:
            return None
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            found: List[str] = []
            target_pids = set(process_ids)

            @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            def enum_proc(hwnd, _lparam):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in target_pids and user32.IsWindowVisible(hwnd):
                    cls_buf = ctypes.create_unicode_buffer(64)
                    user32.GetClassNameW(hwnd, cls_buf, 64)
                    if cls_buf.value == '#32770':
                        title_buf = ctypes.create_unicode_buffer(256)
                        user32.GetWindowTextW(hwnd, title_buf, 256)
                        found.append(title_buf.value or 'untitled dialog')
                return True

            user32.EnumWindows(enum_proc, 0)
            return found[0] if found else None
        except Exception as e:
            logger.warning(f"Could not check for SAP2000 dialogs: {e}")
            return None

    def _sap2000_dialog_blocker_message(self) -> Optional[str]:
        dialog = self._get_sap2000_modal_dialog()
        if dialog:
            return (
                f"SAP2000 is showing a dialog box ('{dialog}') and cannot accept "
                "commands until it is answered. Please switch to SAP2000, respond "
                "to the dialog, and try again."
            )
        return None

    def _detect_elevation_mismatch(self) -> Optional[str]:
        """Return a precise message if Compass and SAP2000 differ in elevation."""
        process_ids = self._get_sap2000_process_ids() or []
        if not process_ids:
            return None
        own = self._is_process_elevated(os.getpid())
        sap = self._is_process_elevated(process_ids[0])
        if own is None or sap is None or own == sap:
            return None
        if own and not sap:
            return (
                "Compass is running as Administrator, but SAP2000 is not. "
                "Windows blocks communication between the two in this case. "
                "Please close Compass and start it normally (without 'Run as "
                "administrator'), then click Connect again."
            )
        return (
            "SAP2000 is running as Administrator, but Compass is not. "
            "Windows blocks communication between the two in this case. "
            "Please restart SAP2000 normally (without 'Run as administrator'), "
            "or run Compass as Administrator too, then click Connect again."
        )

    def _diagnose_connection_failure(self) -> str:
        """Build an actionable error message for a failed COM connection."""
        running = self._is_sap2000_process_running()
        if running is False:
            return (
                "SAP2000 is not running. Please start SAP2000, open (or create) "
                "your model, and then click Connect again."
            )
        if running is True:
            mismatch = self._detect_elevation_mismatch()
            if mismatch:
                return mismatch
            return (
                "SAP2000 is running but Compass could not attach to it. This is "
                "usually a Windows permission mismatch: if SAP2000 was started "
                "'as Administrator', Compass must also run as Administrator (and "
                "vice versa). Restart both applications at the same privilege "
                "level and try again. Also make sure SAP2000 has finished "
                "loading and is not showing a modal dialog."
            )
        return (
            "Failed to connect to SAP2000. Make sure SAP2000 is installed and "
            "running, then try again."
        )

    def _attach_to_running_sap2000(self):
        """Attach to an already-running SAP2000 COM server without launching SAP2000."""
        errors = []
        helper = None

        try:
            helper = comtypes.client.CreateObject('SAP2000v1.Helper')
            # The wrapper module is generated by the CreateObject call above.
            # Import it as `from ... import` so the name `comtypes` stays a
            # module-level reference (a plain `import comtypes.gen.X` here
            # would shadow it as a local and break CreateObject).
            from comtypes.gen import SAP2000v1
            helper = helper.QueryInterface(SAP2000v1.cHelper) #type: ignore
            sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
            if sap_object is not None:
                return sap_object
            errors.append("SAP2000 helper returned no active SapObject")
        except Exception as e:
            errors.append(f"SAP2000 helper attach failed: {e}")

        if helper is not None:
            process_ids = self._get_sap2000_process_ids() or []
            for pid in process_ids:
                try:
                    sap_object = helper.GetObjectProcess("CSI.SAP2000.API.SapObject", pid)
                    if sap_object is not None:
                        logger.info(f"Attached to SAP2000 process {pid}")
                        return sap_object
                    errors.append(f"SAP2000 process {pid} returned no SapObject")
                except Exception as e:
                    errors.append(f"SAP2000 process {pid} attach failed: {e}")

        try:
            sap_object = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
            if sap_object is not None:
                return sap_object
            errors.append("COM active-object lookup returned no SapObject")
        except Exception as e:
            errors.append(f"COM active-object lookup failed: {e}")

        raise RuntimeError("; ".join(errors))

    def _try_connect(self) -> bool:
        try:
            logger.info("Attempting to connect to SAP2000...")
            self._connection_status = "CONNECTING"
            self._last_connect_error = None
            self.sap_object = self._attach_to_running_sap2000()
            if self.sap_object is None:
                raise RuntimeError("Could not attach to an existing SAP2000 instance.")

            # Store raw SAP model first
            raw_sap_model = self.sap_object.SapModel
            if raw_sap_model is None:
                raise RuntimeError("Attached SAP2000 object did not expose a SapModel.")

            # Always create CustomSAP2000Model, with or without config
            self.sap_model = CustomSAP2000Model(raw_sap_model, self.config)

            if self.sap_model is None:
                self._connection_status = "DISCONNECTED"
                raise Exception("Failed to connect to SAP2000.")

            # Get program info from the custom model (it forwards to the raw model)
            info = self.sap_model.GetProgramInfo()
            self._refresh_model_context()

            logger.info(f"Successfully connected to SAP2000 (Version: {info[0]}, Build: {info[1]})")
            self._connected = True
            self._connection_status = "CONNECTED"
            return True
        except OSError as e:
            # COM class not registered => SAP2000 not installed on this machine
            logger.error(f"SAP2000 COM class unavailable: {e}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._last_connect_error = (
                "SAP2000 does not appear to be installed on this computer "
                "(its automation interface is not registered). Install CSI "
                "SAP2000 and try again."
            )
            self._connected = False
            self._connection_status = "DISCONNECTED"
            return False
        except Exception as e:
            logger.error(f"Failed to connect to SAP2000: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._last_connect_error = self._diagnose_connection_failure()
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
            note = ""
            try:
                model_file = self.sap_model.GetModelFilename() #type: ignore
                if not model_file:
                    note = " Note: no model file is open yet - open or create a model in SAP2000."
            except Exception:
                pass
            return ToolResult(text=f"Successfully connected to SAP2000.{note}")
        else:
            return ToolResult(error=self._last_connect_error or
                              "Failed to connect to SAP2000. Make sure SAP2000 is running.")
    
    # New method to explicitly load configuration
    async def load_sap_config(self, config_path=None) -> ToolResult:
        """Explicitly load SAP2000 configuration."""
        if self._load_config(config_path):
            # If we have an existing CustomSAP2000Model, update its config
            if self.sap_model and hasattr(self.sap_model, 'update_config') and self.config is not None:
                self.sap_model.update_config(self.config)
                self._refresh_model_context()
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
                    if not self.model_path:
                        self._refresh_model_context()
                    ret = self.sap_model.View.RefreshView(0, False) #type: ignore
                    if ret != 0:
                        error_text = f"\nFailed to refresh view (return code: {ret})"
                    else:
                        error_text = ""

                    if self.model_path:
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

The connection to SAP2000 is established explicitly through the SAP connection button before SAP actions run.
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

The connection to SAP2000 is established explicitly through the SAP connection button before SAP actions run.
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
