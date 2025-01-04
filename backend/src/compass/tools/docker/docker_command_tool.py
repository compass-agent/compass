from typing import Literal
from pathlib import Path
from ...tools.base import BaseAnthropicTool, ToolResult
import asyncio
import logging
from ...constants import DOCKER_CONTAINER_NAME, DOCKER_WORKING_DIR

logger = logging.getLogger(__name__)

class DockerCommandTool(BaseAnthropicTool):
    name: Literal["docker_command"] = "docker_command"
    
    def __init__(self):
        self.container_name = DOCKER_CONTAINER_NAME
        self.container_working_dir = Path(DOCKER_WORKING_DIR)

    async def __call__(
        self,
        *,
        command: str,
    ) -> ToolResult:
        """Execute command in Docker container"""
        try:
            # Build command with fixed working directory
            docker_command = f"docker exec {self.container_name} bash -c 'cd {self.container_working_dir} && {command}'"
            
            logger.info(f"Executing docker command: {docker_command}")
            
            process = await asyncio.create_subprocess_shell(
                docker_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return ToolResult(error=f"Command failed: {stderr.decode()}")
            
            return ToolResult(
                output=stdout.decode(),
                system=f"Command executed: {command}" if stderr.decode() else None
            )
            
        except Exception as e:
            return ToolResult(error=str(e))

    def to_params(self):
        return {
            "name": self.name,
            "description": "Execute commands in OpenFOAM Docker container",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute in OpenFOAM container"
                    }
                },
                "required": ["command"]
            }
        } 