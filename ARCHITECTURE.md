# Compass System Architecture & Design Specification

Compass is a Windows desktop application that acts as an AI co-pilot for engineering software. It automates structural modeling, load applications, member optimization, and queries CSI SAP2000 using a custom COM interop interface and a RAG (Retrieval-Augmented Generation) system.

---

## 1. High-Level System Architecture

Compass is built using a dual-process architecture to separate the high-performance desktop control and AI orchestration logic from the cross-platform presentation shell:

```mermaid
graph TD
    subgraph Frontend (Electron / React Shell)
        A[main.js - Electron Main Process] <-->|IPC| B[preload.js - Context Bridge]
        B <-->|React Context| C[React Renderer - UI Elements]
        C <-->|InitSapConfig.js| D[YAML Configuration Editor]
        C <-->|ControlPanel.js| E[Agent Controls & Modes]
    end

    subgraph Backend (Python Flask / Socket.IO)
        F[app.py - Flask Server] <-->|Socket.IO port 5001| C
        F <-->|Eventlet Hub| G[AgentService - Orchestrator]
        G <-->|LLMFactory| H[LLM Providers: Anthropic / Google]
        G <-->|ToolCollection| I[Available Tools]
        I <-->|sap_com| J[SAPComTool]
        J <-->|comtypes client| K[CSI SAP2000 Application]
        J <-->|SAPAPIQuery| L[ChromaDB Vector DB]
    end
```

### Key Components

*   **Electron Shell (Frontend)**: Runs a chromium-based UI built with React. It uses Webpack for compilation and Electron IPC for local hardware events. Toggles between Manual, Semi-Automatic, and Automatic agent execution modes.
*   **Flask-SocketIO Server (Backend)**: Runs a Python service inside a virtual environment (`.venv`). It is monkey-patched with `eventlet` for asynchronous Socket.IO event handling, communicating with the React UI via real-time WebSocket events on `http://localhost:5001`.
*   **Agent Service (Orchestrator)**: Manages message history, AI response streaming, cursor/screenshot capturing, and schedules tool invocations.

---

## 2. Structural Engineering Agent & RAG System

The AI structural copilot operates through a customized LLM execution loop supporting tool-calling and context-injection.

### Agent Execution Loop
1. **Manual / Semi-Auto Mode**: The user enters a request (e.g., *"generate deck area loads at 14ft elevation"*). The agent analyzes the model state, proposes a list of Python scripts/commands, and yields control back to the UI. The user clicks **Execute** to approve the tool call.
2. **Auto Mode**: The agent processes user commands in a recursive loop (`_process_message_loop`), automatically executing tools and refining actions for up to `MAX_ITERATIONS` (default `20`).

### Retrieval-Augmented Generation (RAG)
To query the extensive SAP2000 COM API documentation, the system uses a RAG pipeline:
*   **Vector Database**: ChromaDB (`chromadb.PersistentClient`) with SQLite storage (`chroma.sqlite3`).
*   **Embeddings**: OpenAI's `text-embedding-3-small` model is used to compute semantic query vectors.
*   **Seeding Data**: The database is compiled from SAP2000 PDF documentations (parsed into function-level chunks in `training/sap2000_rag/`). It queries the vector database for documentation matches whenever the agent needs to generate Python scripts.

---

## 3. SAP2000 COM Integration

The connection to SAP2000 is established through Windows COM (Component Object Model) using the `comtypes` package:

```python
helper = comtypes.client.CreateObject('SAP2000v1.Helper')
helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
self.sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
self.sap_model = CustomSAP2000Model(self.sap_object.SapModel, self.config)
```

### Custom Model Wrapper (`CustomSAP2000Model`)
Rather than calling basic API functions directly, the backend wraps the raw SAP2000 model in `CustomSAP2000Model` ([custom_model.py](file:///c:/Users/mksad/Projects/compass/backend/src/compass/tools/sap2000/core/custom_model.py)). This class implements advanced structural modeling routines:

*   **Column Base Restraint Assignment (`add_base_restraints`)**: Automatically crawls all frame coordinates, maps grid connectivity, identifies bottom-most column nodes (with no frames connecting below them), and restrains them (defaulting to translation-fixed, rotation-free).
*   **Floor Area Polygon Detection (`add_floor_areas`)**:
    1. Collects all horizontal beams at a target elevation $Z$.
    2. Builds a 2D planar graph representation of the grid.
    3. Sorts structural edges by angle around each vertex.
    4. Runs a **Graph Face Traversal** algorithm to find closed quadrilaterals.
    5. Dynamically creates area objects in SAP2000 for each closed face.
*   **Frame Grouping & Categorization (`get_columns_info` / `get_beams_info`)**: Extracts boundary extremes to classify columns as `corner`, `edge`, or `interior`. Groups beam segments based on physical length tolerances to optimize member grouping.

---

## 4. Packaging & Distribution Process

The application is built as a React/Electron shell plus a PyInstaller onedir backend:

```
[PyInstaller]      -> backend/src/compass/app.py -> backend/dist/compass_backend/compass_backend.exe
[Webpack]          -> frontend/renderer/*.js     -> frontend/renderer/dist/
[electron-builder] -> package.json extraResources -> resources/backend/compass_backend/
```

1. **Backend Packaging**: PyInstaller uses [compass_backend.spec](file:///c:/Users/mksad/Projects/compass/backend/compass_backend.spec) to create an onedir bundle. The spec bundles Compass data files, prompts, config defaults, SAP2000 RAG seed data, and section tables. Heavy optional ML packages such as torch, torchvision, ultralytics, easyocr, transformers, scipy, and sklearn are excluded; YOLO icon detection degrades gracefully when they are not present.
2. **Frontend Compiling**: Webpack builds `app.bundle.js` and `templateTraining.bundle.js` into `frontend/renderer/dist/`.
3. **App Distribution**: `electron-builder` reads the `build` section in [package.json](file:///c:/Users/mksad/Projects/compass/package.json). The backend onedir folder is included through `extraResources` as `resources/backend/compass_backend`; there is no `build-config.js` copy hook anymore.
4. **Unsigned Local Windows Builds**: `win.signAndEditExecutable` is disabled because this repo does not configure a signing certificate. This avoids electron-builder's `winCodeSign` helper extraction path, which can fail on Windows accounts without symlink creation privilege. The NSIS installer still builds; enable executable editing/signing again in a signed CI/release environment if app executable version/icon resources must be stamped.
5. **Runtime Data Layout**: Packaged installs treat the app directory as read-only. Writable state lives under `%APPDATA%/Compass`, while user-facing generated models/configs live under `Documents/Compass`.

---

## 5. Production Runtime Path Model

The backend centralizes path decisions in [runtime_paths.py](file:///c:/Users/mksad/Projects/compass/backend/src/compass/runtime_paths.py):

* **Read-only bundled data**: `get_bundle_dir()` points at the PyInstaller `_internal` data root when frozen, and `backend/src` in development.
* **Writable app data**: `get_appdata_dir()` creates `%APPDATA%/Compass` for settings, logs, copied seed databases, and comtypes generated wrappers.
* **Workspace artifacts**: `get_workspace_dir()` prefers `WORKSPACE_FOLDER`, then `Documents/Compass` in frozen mode, then the repo root in development.
* **RAG database**: `seed_user_data()` copies bundled `compass/database/sap2000_api` into `%APPDATA%/Compass/database/sap2000_api` and tracks a seed fingerprint.
* **Template DB**: `template_database.db` is writable in AppData when frozen, and remains in `backend/src/compass/database` during development.
* **COM wrapper cache**: `setup_comtypes_cache()` redirects generated `comtypes.gen` wrappers to `%APPDATA%/Compass/comtypes_gen` in frozen mode.

---

## 6. Fixed Historical Packaging & Connection Issues

The following historical failure modes have been addressed in the current codebase:

* **Production backend lifecycle**: [main.js](file:///c:/Users/mksad/Projects/compass/frontend/main/main.js) starts the packaged backend during `app.whenReady()` when `app.isPackaged` is true. [backendManager.js](file:///c:/Users/mksad/Projects/compass/frontend/main/backendManager.js) locates the onedir executable, sets `COMPASS_ENV=production`, passes `WORKSPACE_FOLDER`, logs to `%APPDATA%/Compass/logs/electron_main.log`, and stops/restarts the process when needed.
* **Executable naming/layout**: PyInstaller produces `backend/dist/compass_backend/compass_backend.exe`, and `package.json` copies that onedir folder into `resources/backend/compass_backend`.
* **Keyless first-run boot**: Missing LLM keys no longer crash the backend. The backend emits `backend_status`; the renderer shows onboarding/settings and can validate/save keys through IPC and Socket.IO events.
* **Writable frozen paths**: Logs, settings, template DB, Chroma seed data, generated comtypes wrappers, SAP config output, and generated model files no longer rely on writing inside Program Files or the PyInstaller bundle.
* **SAP2000 attach diagnostics**: SAP COM connection failures now distinguish "SAP2000 is not running", "COM class not registered", and the likely UAC privilege mismatch where SAP2000 and Compass are running at different privilege levels.
* **Agent Hub backend events**: The renderer's `agent_hub` and `delete_page` events are backed by an `Agent` database table and import/export/list/create/update/delete handlers.

---

## 7. Verification Status

Current automated/local checks:

* `npm run build` completes successfully, with only Webpack bundle-size warnings.
* Backend Python modules compile successfully with `python -m compileall`.
* Development backend boot reaches Socket.IO polling HTTP 200.
* Standalone `backend/dist/compass_backend/compass_backend.exe` boots in a fresh AppData sandbox, serves Socket.IO polling HTTP 200, seeds Chroma/template data, and creates the writable comtypes cache.
* `npm run package-win` creates `dist/Compass-Setup-1.0.0.exe`.
* `dist/win-unpacked/Compass.exe` launches the packaged backend and reaches Socket.IO polling HTTP 200.
* The NSIS installer installs successfully into a temporary per-user directory; the installed app launches the packaged backend and reaches Socket.IO polling HTTP 200; silent uninstall returns success.
* The PyInstaller bundle excludes torch/ultralytics from collected files.

Manual checks still needed on a SAP2000 workstation:

* **Primary acceptance check**: Open the packaged/installed Compass app while SAP2000 is already running, use Tools > SAP2000 Scripting > Connect, then ask the chat agent for a tiny SAP interaction such as "Check the SAP2000 connection and tell me the program version and current model filename" or "Create a new blank SAP2000 model and report the return code." The check passes when the agent executes the SAP COM tool and reports a successful result from SAP2000.
* Load a generated `.sapConfig.yml`, run a small COM write/save action, and verify the model is saved under `Documents/Compass/models`.
* Confirm behavior when SAP2000 and Compass are launched with mismatched privilege levels.
