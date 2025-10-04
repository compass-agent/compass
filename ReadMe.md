# Compass

> Windows desktop app that augments engineering workflows with an AI agent and software integrations.

## Overview
Compass is a Windows desktop application that acts as an AI co‑pilot for engineering software. It automates common tasks, reduces learning curves, and accelerates engineering workflows.

## Highlights
- Windows desktop app with AI agent that operates engineering software
- AgentHub to create, export, and import specialized domain agents
- Integrated with SAP2000 as the first application through COM scripting and UI control

## Demo
See the demo and overview at: [https://compass-agent.github.io/compass](https://compass-agent.github.io/compass)

## Quick Start

> **Prerequisites:** Windows 10/11, [Node.js](https://nodejs.org/) ≥ 16, [Python](https://python.org/downloads/) ≥ 3.11

**Option 1: One-command setup and run**
```bash
# First time setup (creates venv, installs all dependencies)
npm run setup

# Daily development (starts both backend + frontend)
npm run dev
```

**Option 2: Manual setup**
```powershell
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
npm install

# Run
npm run dev
```

4) Set LLM API keys
Create `backend/src/compass/key.py` with your keys:
```python
# backend/src/compass/key.py
ANTHROPIC_API_KEY = "your_anthropic_api_key"
GOOGLE_API_KEY = "your_gemini_api_key"
OPENAI_API_KEY = "your_openai_api_key"  # used by SAP API RAG
```
Provider selection is configured in `backend/src/compass/constants.py` via `LLM_PROVIDER` ("anthropic" or "google").

Troubleshooting
- If `webpack` or `cross-env` is not recognized, run `npm install` in the repo root.
- If imports fail when running the backend, ensure `PYTHONPATH` includes `backend/src` (the debug config sets this automatically).

## Architecture at a Glance
Electron desktop app with React frontend and Flask backend. The two communicate via Socket.IO for real-time interaction.

## Contributing
Contributions are welcome. Please open an issue to discuss major changes before submitting a PR.

## License
MIT License. You may use, modify, and distribute this software provided you include the original copyright and license notice.