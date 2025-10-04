# Compass

> Windows desktop app that augments engineering workflows with an AI agent and software integrations.

## Overview
Compass is a Windows desktop application that acts as an AI co‑pilot for engineering software. It combines an Electron/React UI with a local Python/Flask backend to automate common tasks, operate tools like SAP2000 via COM, and accelerate workflows with screen parsing and specialized agents.

## Highlights
- Windows desktop app with Electron/React frontend and local Flask backend
- AI agent that can operate engineering software (e.g., SAP2000; Ansys/AutoCAD planned)
- AgentHub to create, export, and import specialized domain agents
- Screen parsing with template matching (and optional YOLO) to identify UI elements
- SAP2000 COM automation for modeling/analysis operations
- RAG-backed assistance for SAP2000 API (prebuilt vector DB included)

## Demo & Screenshots
See the demo on the project website (Demo section). Add screenshots/GIFs here for quick reference.

## Quick Start
Prerequisites: Windows 10/11, Node.js ≥ 16, Python ≥ 3.11

1) Install frontend deps
```bash
npm install
```

2) Create venv and install deps
```powershell
python -m venv .venv
\.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```
Optional: If you prefer the venv under backend instead, use:
```powershell
cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; cd ..
```

3) Run
```powershell
# Backend (in one terminal)
python backend/src/compass/app.py

# Frontend (in another terminal)
npm run watch
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

## Requirements & Integrations
- Windows-only runtime; designed and tested for Windows 10/11
- SAP2000 (licensed and installed) required for SAP-specific features
- Prebuilt Chroma vector database included for SAP2000 API RAG; regeneration instructions in docs

## Architecture at a Glance
Electron/React frontend communicates with a local Flask backend via Socket.IO. The backend exposes tools for screen parsing, SAP2000 COM automation, and agent workflows; optional RAG enhances API assistance. See the architecture diagram in docs.

## Documentation
See the project website for the Demo and overview. Detailed docs will live on the repo's GitHub Pages site.

## Contributing
Contributions are welcome. Please open an issue to discuss major changes before submitting a PR.

## License
MIT License (recommended). You may use, modify, and distribute this software provided you include the original copyright and license notice.