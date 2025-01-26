from typing import Literal
from pathlib import Path
from anthropic.types.beta import BetaToolUnionParam
from ...tools.base import BaseTool
from compass.types.agent import ToolResult
import asyncio
import logging
from ...constants import DOCKER_CONTAINER_NAME, DOCKER_WORKING_DIR
import subprocess
import platform
import os


logger = logging.getLogger(__name__)

class BashExecutor(BaseTool):
    name: Literal["bash_run"] = "bash_run"
    
    def __init__(self):
        self.container_name = DOCKER_CONTAINER_NAME
        self.container_working_dir = Path(DOCKER_WORKING_DIR)
        # Get host IP for X11 forwarding
        try:
            if platform.system() == "Darwin":  # macOS
                command = "ifconfig en0 | grep inet | awk '$1==\"inet\" {print $2}'"
            elif platform.system() == "Linux":  # Linux
                command = "hostname -I | awk '{print $1}'"
            elif platform.system() == "Windows":  # Windows
                command = "powershell -Command \"(ipconfig | findstr 'IPv4' | findstr '192.168.0.') -replace '^.*: ', ''\""
            else:
                raise ValueError("Unsupported operating system")
            self.host_ip = subprocess.check_output(command, 
            shell=True
            ).decode().strip()
            logger.info(f"SPZ , {self.host_ip}")
            # Set up X11 permissions
            if platform.system() == "Darwin":  # macOS
                subprocess.run(f"xhost + {self.host_ip}", shell=True)
            elif platform.system() == "Linux":  # Linux
                subprocess.run(f"xhost + {self.host_ip}", shell=True)
            elif platform.system() == "Windows":  # Windows
                if not os.environ.get("DISPLAY"):
                    os.environ["DISPLAY"] = "localhost:0.0"
                logger.info(f"Windows X11: DISPLAY set to {os.environ['DISPLAY']}")
                # Check if X server is running
                try:
                    # Use PowerShell's Get-Process to check for vcxsrv.exe
                    result = subprocess.run(
                        ["powershell", "-Command", "Get-Process -Name vcxsrv"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        logger.info("Windows X11: VcXsrv is running.")
                    else:
                        logger.warning("Windows X11: VcXsrv is not running.")
                except Exception as e:
                    logger.error(f"Error checking X server: {e}")
            else:
                raise ValueError("Unsupported operating system")
        except Exception as e:
            logger.warning(f"Failed to set up X11 forwarding: {e}")
            self.host_ip = None

    async def __call__(
        self,
        *,
        runtime: Literal["host", "docker"],
        script: str,
    ) -> ToolResult:
        """Execute bash script either in Docker container or on host system"""
        try:
            # Determine if command should run in background
            run_detached = "paraFoam --server" in script
            
            if runtime == "docker":
                # Base command with OpenFOAM environment setup
                base_cmd = f"source /opt/openfoam8/etc/bashrc && cd {self.container_working_dir}"
                
                # Add command execution part
                if run_detached:
                    exec_cmd = f"nohup {script} > /dev/null 2>&1 & echo $!"
                else:
                    exec_cmd = script
                
                # Add X11 forwarding if available and running ParaView
                display_env = f"-e DISPLAY={self.host_ip}:0" if self.host_ip and "paraFoam" in script else ""
                full_command = f"docker exec {display_env} {self.container_name} bash -c '{base_cmd} && {exec_cmd}'"
            elif runtime == "host":
                full_command = script
            else:
                return ToolResult(error=f"Invalid runtime: {runtime}. Must be either 'host' or 'docker'")
            
            logger.info(f"Executing {runtime} script: {full_command}")
            
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return ToolResult(error=f"Script execution failed: {stderr.decode()}")
            
            if run_detached:
                return ToolResult(
                    text="Background process started successfully",
                    system=f"Command running in background: {script}"
                )
            
            return ToolResult(
                text=stdout.decode(),
                system=f"Script executed in {runtime}: {script}" if stderr.decode() else None
            )
            
        except Exception as e:
            return ToolResult(error=str(e))

    def to_params(self) -> BetaToolUnionParam:
        return {
            "name": self.name,
            "description": """Execute bash scripts either in OpenFOAM Docker container or on host system.
When runtime='docker', the script will be executed inside the OpenFOAM container with proper environment setup.
Example: script='ls' becomes 'docker exec container_name bash -c \"source /opt/openfoam8/etc/bashrc && cd /work_dir && ls\"'

When runtime='host', the script executes directly on the host machine.
Example: script='ls' executes as-is on the host machine.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "runtime": {
                        "type": "string",
                        "enum": ["host", "docker"],
                        "description": "Where to execute the script: 'host' for local system, 'docker' for OpenFOAM container with environment setup"
                    },
                    "script": {
                        "type": "string",
                        "description": "The bash script to execute (will be wrapped with Docker and OpenFOAM setup if runtime='docker')"
                    }
                },
                "required": ["runtime", "script"]
            }
        } # type: ignore 