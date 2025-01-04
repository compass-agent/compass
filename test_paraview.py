import subprocess
import time
import logging
from pathlib import Path
import asyncio
import socket

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def is_port_open(port, host='localhost'):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

async def main():
    try:
        # 1. Setup X11 forwarding
        host_ip = subprocess.check_output(
            "ifconfig en0 | grep inet | awk '$1==\"inet\" {print $2}'", 
            shell=True
        ).decode().strip()
        logger.debug(f"Host IP: {host_ip}")
        
        # Setup X11 permissions
        subprocess.run(f"xhost + {host_ip}", shell=True)
        logger.debug("X11 permissions set")

        # 2. Launch ParaView server in Docker
        container_name = "recursing_mirzakhani"
        working_dir = "/home/openfoam/run/sample"
        
        # Launch ParaView in background
        paraview_cmd = f"docker exec -e DISPLAY={host_ip}:0 {container_name} bash -c 'source /opt/openfoam8/etc/bashrc && cd {working_dir} && nohup paraFoam --server > paraview.log 2>&1 &'"
        logger.debug(f"Launching ParaView with command: {paraview_cmd}")
        
        subprocess.run(paraview_cmd, shell=True)
        
        # Wait for ParaView to initialize and check if server is running
        logger.debug("Waiting for ParaView server to start...")
        max_attempts = 10
        for i in range(max_attempts):
            if is_port_open(11111):
                logger.debug("ParaView server is running!")
                break
            logger.debug(f"Waiting for server... attempt {i+1}/{max_attempts}")
            await asyncio.sleep(1)
        else:
            raise Exception("ParaView server failed to start")

        # 3. Create the Python script file locally first
        test_script = '''from paraview.simple import *
import sys

# Set timeout for connection
from paraview.servermanager import vtkProcessModule
vtkProcessModule.GetProcessModule().SetExitTimeout(10)

try:
    Connect("localhost:11111")
    print("Connected to ParaView server!")
    view = GetActiveView()
    if not view:
        view = CreateRenderView()
    print("Created/got view successfully!")
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    sys.exit(1)
'''
        temp_script = Path("/tmp/test_paraview_commands.py")
        temp_script.write_text(test_script)
        logger.debug(f"Created local script with content:\n{test_script}")

        # 4. Copy the script to container and execute with timeout
        docker_cmd = f"""
        docker cp {temp_script} {container_name}:/tmp/test_paraview_commands.py &&
        docker exec {container_name} bash -c '
            source /opt/openfoam8/etc/bashrc &&
            timeout 10s pvpython /tmp/test_paraview_commands.py'
        """
        
        logger.debug("Executing ParaView Python commands...")
        result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
        logger.debug(f"pvpython stdout: {result.stdout}")
        logger.debug(f"pvpython stderr: {result.stderr}")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
    finally:
        # Cleanup
        logger.debug("Cleaning up...")
        try:
            temp_script.unlink(missing_ok=True)
            subprocess.run(f"docker exec {container_name} rm -f /tmp/test_paraview_commands.py", shell=True)
            subprocess.run(f"docker exec {container_name} pkill -f paraFoam", shell=True)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 