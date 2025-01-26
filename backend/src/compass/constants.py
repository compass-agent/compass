import os

# Agent constants:
MAX_ITERATIONS = 20 # Maximum number of iterations for the agent in auto Mode


# LLM constants:
# Generic:
MAX_TOKENS = 1024

# Anthropic Provider:
PROMPT_CACHING = True
ANTHROPIC_MODEL_NAME_MANUAL = "claude-3-5-sonnet-latest"
ANTHROPIC_MODEL_NAME_AUTO = "claude-3-5-sonnet-latest"

# Google Provider:
GOOGLE_MODEL_NAME = "gemini-2.0-flash-exp"
## Tools constants:
# Screenshot constants:
SCREENSHOT_OPTIMIZATION = False
SCREENSHOT_SCALE_FACTOR = 1  # Reduce resolution by X%
SCREENSHOT_COLOR_DEPTH = 8     # 8-bit color depth (256 colors)
KEEP_SCREENSHOTS = True        # Keep screenshots after use
PRE_RUN_SCREENSHOTS = True     # Take screenshots before running the agent

# Mouse click constants
ENABLE_SCREEN_DESCRIPTION_MOUSE_CLICK = True
ENABLE_SCREENSHOT_COMPARISON_MOUSE_CLICK = True

# Screenshot constants
ENABLE_SCREEN_DESCRIPTION_SCREENSHOT = True
ENABLE_SCREENSHOT_COMPARISON_SCREENSHOT = True



## PARAMETERS SET  BY USER
# For now, we only set these here. But in the future, we will allow set them in the UI.

# Agent selection. For now, we only have OpenFoam. But in the future, we will have more agents.
AGENT_NAME = "OpenFoam" # OpenFoam Or Generic or FreeCAD  # Generic is the default basic agent

# Below are the parameters for the OpenFoam agent
DOCKER_CONTAINER_NAME = "recursing_mirzakhani"
DOCKER_WORKING_DIR = "/home/openfoam/run"
# Get the current user's home directory
HOME_DIR = os.path.expanduser("~")
HOST_WORKING_DIR = os.path.join(HOME_DIR, "openfoam", "run")
# HOST_WORKING_DIR = "/Users/kazem/openfoam/run/"
# Screenshot configuration

# Define tool configurations for different agents
TOOL_TYPES = {
    "computer": "computer_20241022",
    "file": "text_editor_20241022",
    "bash": "command_20241022"
}

AGENT_TOOLS = {
    "OpenFoam": [
        {"name": "bash", "type": TOOL_TYPES["bash"]},
        {"name": "file", "type": TOOL_TYPES["file"]}
    ],
    "FreeCAD": [
        {"name": "computer", "type": TOOL_TYPES["computer"]}
    ],
    "Generic": [
        {"name": "computer", "type": TOOL_TYPES["computer"]},
        {"name": "file", "type": TOOL_TYPES["file"]},
        {"name": "bash", "type": TOOL_TYPES["bash"]}
    ]
}

# LLM Provider Configuration
LLM_PROVIDER = "anthropic"  # Options: "anthropic" or "google"
