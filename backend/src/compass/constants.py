import os

# Agent constants:
MAX_ITERATIONS = 20 # Maximum number of iterations for the agent in auto Mode
DEFAULT_AGENT_TYPE = "structural-engineer"  # Default agent type to use


# LLM constants:
# Generic:
MAX_TOKENS = 4096

# Anthropic Provider:
PROMPT_CACHING = True
ANTHROPIC_MODEL_NAME_MANUAL = "claude-sonnet-4-20250514" # claude-3-7-sonnet-20250219 "claude-3-5-sonnet-latest"
ANTHROPIC_MODEL_NAME_AUTO = "claude-sonnet-4-20250514" # claude-3-7-sonnet-20250219 "claude-3-5-sonnet-latest"

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
TIME_TO_WAIT_AFTER_CLICK_BEFORE_SCREENSHOT = 0.1

# Screenshot constants
ENABLE_SCREEN_DESCRIPTION_SCREENSHOT = True
ENABLE_SCREENSHOT_COMPARISON_SCREENSHOT = True

## PARAMETERS SET  BY USER
# Below are the parameters for the OpenFoam agent
DOCKER_CONTAINER_NAME = "recursing_mirzakhani"
DOCKER_WORKING_DIR = "/home/openfoam/run"
# Get the current user's home directory
HOME_DIR = os.path.expanduser("~")
HOST_WORKING_DIR = os.path.join(HOME_DIR, "openfoam", "run")
# HOST_WORKING_DIR = "/Users/kazem/openfoam/run/"
# Screenshot configuration

# Define tool configurations for different agents
AGENT_TOOLS = {
    "OpenFoam": ["bash", "file"],
    "FreeCAD": ["computer", "bash", "file"],
    "Generic": ["computer", "file", "bash"],
    "structural-engineer": ["sap_com", "computer"]  # Needs SAP and desktop tools
}

# LLM Provider Configuration
LLM_PROVIDER = "anthropic"  # Options: "anthropic" or "google"
