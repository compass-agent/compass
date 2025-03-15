# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Set environment variables
$env:FLASK_APP = "compass.app"
$env:FLASK_DEBUG = "1"
$env:PYTHONPATH = "$PWD\src"

# Change to the src directory
cd src

# Run the Flask app
python -m compass.app

# Keep the window open
Read-Host -Prompt "Press Enter to exit" 