import logging
from typing import Literal
from pathlib import Path
import time
from ...tools.base import BaseTool, ToolResult
from ...constants import HOST_WORKING_DIR

logger = logging.getLogger(__name__)

class ParaViewTool(BaseTool):
    name: Literal["paraview"] = "paraview"
    
    def __init__(self):
        self.working_dir = Path(HOST_WORKING_DIR)
        # Default ParaView server connection settings
        self.server_host = "localhost"
        self.server_port = 11111  # Default ParaView server port

    async def __call__(
        self,
        *,
        script: str,
    ) -> ToolResult:
        """Execute ParaView Python commands in the active session"""
        try:
            start_time = time.time()
            
            # Create a temporary Python script file
            script_path = self.working_dir / ".temp_paraview_script.py"
            
            # Add necessary imports and server connection
            full_script = (
                "from paraview.simple import *\n"
                f"Connect('{self.server_host}:{self.server_port}')\n"
                f"{script}\n"
            )
            
            with open(script_path, 'w') as f:
                f.write(full_script)
            
            # Execute the script using pvpython
            import subprocess
            process = await subprocess.create_subprocess_exec(
                'pvpython',
                str(script_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time
            
            # Clean up temp file
            script_path.unlink()
            
            if process.returncode != 0:
                return ToolResult(
                    error=f"ParaView script failed:\n{stderr.decode()}",
                    system=f"Execution time: {execution_time:.2f}s"
                )
            
            return ToolResult(
                output=stdout.decode(),
                system=f"Execution time: {execution_time:.2f}s"
            )
            
        except Exception as e:
            return ToolResult(error=str(e))

    def to_params(self) -> dict:
        return {
            "name": self.name,
            "description": """Execute ParaView Python commands for visualization tasks.
Example commands:
- Load data: reader = OpenFOAMReader(FileName='case.foam')
- Apply filters: contour = Contour(Input=reader)
- Change view: camera = GetActiveCamera()
- Show mesh: Show(reader, renderView1, 'UnstructuredGridRepresentation')""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "ParaView Python script to execute"
                    }
                },
                "required": ["script"]
            }
        } 