# Compass

> Windows desktop app that augments engineering workflows with an AI agent and software integrations.

[![Website](https://img.shields.io/badge/Website-Visit-blue)](https://compass-agent.github.io/compass)
[![Architecture](https://img.shields.io/badge/📖-Architecture-green)](./ARCHITECTURE.md)

## Overview
Compass is a Windows desktop application that acts as an AI co‑pilot for engineering software. It automates common tasks, reduces learning curves, and accelerates engineering workflows.


## Highlights
- Windows desktop app with AI agent that operates engineering software
- AgentHub to create, export, and import specialized domain agents
- Integrated with SAP2000 as the first application through COM scripting and UI control
- **Educational**: Learn RAG, multi-agent systems, and desktop automation patterns

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

**Set LLM API Keys**

Create `backend/src/compass/key.py` with your keys:
```python
# backend/src/compass/key.py
ANTHROPIC_API_KEY = "your_anthropic_api_key"
```

> **Note**: Currently, the stable version of this repo only accepts the Anthropic Claude model. We are working on stabilizing the Google and OpenAI frontier models as well. 


## Architecture at a Glance
Electron desktop app with React frontend and Flask backend. The two communicate via Socket.IO for real-time interaction.

## Contributing
Contributions are welcome. Please open an issue to discuss major changes before submitting a PR.

## License
MIT License. You may use, modify, and distribute this software provided you include the original copyright and license notice.