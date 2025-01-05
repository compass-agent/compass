from typing import Literal
from pathlib import Path
from anthropic.types.beta import BetaToolUnionParam
from ...tools.base import BaseAnthropicTool, ToolResult
import asyncio
import logging
from ...constants import DOCKER_CONTAINER_NAME, DOCKER_WORKING_DIR

logger = logging.getLogger(__name__)

class CommandTool(BaseAnthropicTool):
    name: Literal["command"] = "command"
    
    def __init__(self):
        self.container_name = DOCKER_CONTAINER_NAME
        self.container_working_dir = Path(DOCKER_WORKING_DIR)

    async def __call__(
        self,
        *,
        environment: Literal["host", "docker"],
        command: str,
    ) -> ToolResult:
        """Execute command either in Docker container or on host system"""
        try:
            if environment == "docker":
                # Build command with OpenFOAM environment and working directory
                full_command = f"docker exec {self.container_name} bash -c 'source /opt/openfoam8/etc/bashrc && cd {self.container_working_dir} && {command}'"
            elif environment == "host":
                full_command = command
            else:
                return ToolResult(error=f"Invalid environment: {environment}. Must be either 'host' or 'docker'")
            
            logger.info(f"Executing {environment} command: {full_command}")
            
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return ToolResult(error=f"Command failed: {stderr.decode()}")
            
            return ToolResult(
                output=stdout.decode(),
                system=f"Command executed in {environment}: {command}" if stderr.decode() else None
            )
            
        except Exception as e:
            return ToolResult(error=str(e))

    def to_params(self) -> BetaToolUnionParam:
        return {
            "name": self.name,
            "description": """Execute commands either in OpenFOAM Docker container or on host system.
When environment='docker', the command will be executed inside the OpenFOAM container with proper environment setup.
Example: command='ls' becomes 'docker exec container_name bash -c \"source /opt/openfoam8/etc/bashrc && cd /work_dir && ls\"'

When environment='host', the command executes directly on the host system.
Example: command='ls' executes as-is on the host machine.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "enum": ["host", "docker"],
                        "description": "Where to execute the command: 'host' for local system, 'docker' for OpenFOAM container with environment setup"
                    },
                    "command": {
                        "type": "string",
                        "description": "The command to execute (will be wrapped with Docker and OpenFOAM setup if environment='docker')"
                    }
                },
                "required": ["environment", "command"]
            }
        } # type: ignore 