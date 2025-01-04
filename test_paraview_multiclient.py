import subprocess
import time
import logging
from pathlib import Path
import asyncio
import socket

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

        container_name = "recursing_mirzakhani"
        working_dir = "/home/openfoam/run/sample"
        
        # Ensure directory exists
        subprocess.run(f"docker exec {container_name} mkdir -p {working_dir}", shell=True)
        
        # Create a dummy case file
        create_case_cmd = f"""docker exec {container_name} bash -c '
            source /opt/openfoam8/etc/bashrc &&
            cd {working_dir} &&
            touch case.foam'"""
        subprocess.run(create_case_cmd, shell=True)
        
        # Launch ParaFoam with automatic "Y" response
        paraview_cmd = f"""docker exec -e DISPLAY={host_ip}:0 {container_name} bash -c '
            source /opt/openfoam8/etc/bashrc &&
            cd {working_dir} &&
            echo "Y" | paraFoam --server > paraview.log 2>&1 &'"""
        
        logger.debug(f"Launching ParaView with command: {paraview_cmd}")
        subprocess.run(paraview_cmd, shell=True)
        
        # Wait a bit for ParaView to start
        await asyncio.sleep(5)
        
        # Try to connect with Python
        test_script = '''from paraview.simple import *
import sys

try:
    # Try to connect to the server
    Connect("localhost:11111")
    print("Connected to ParaView!")
    
    # Create a simple sphere
    sphere = Sphere()
    Show(sphere)
    
    # Get or create a view
    view = GetActiveView()
    if not view:
        view = CreateRenderView()
    
    # Reset camera and render
    view.ResetCamera()
    Render()
    
    print("Successfully created and displayed a sphere!")
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    sys.exit(1)
'''
        temp_script = Path("/tmp/test_paraview_commands.py")
        temp_script.write_text(test_script)
        
        # Execute the Python script in Docker with proper connection parameters
        docker_cmd = f"""docker exec {container_name} bash -c '
            source /opt/openfoam8/etc/bashrc &&
            pvpython --server-url=localhost:11111 /tmp/test_paraview_commands.py'"""
        
        logger.debug("Executing ParaView Python commands...")
        result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
        logger.debug(f"pvpython stdout: {result.stdout}")
        logger.debug(f"pvpython stderr: {result.stderr}")
        
        logger.info("ParaView is running. Press Ctrl+C to exit...")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
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