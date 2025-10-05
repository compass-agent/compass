# Compass Architecture

> **Learn**: This document explains how Compass implements a production-ready agentic AI system for desktop automation, combining computer vision, RAG, and multi-agent orchestration.

---

## 🎯 High-Level Overview

Compass is an AI-powered co-pilot that operates engineering software through a trained agent system. Unlike general-purpose AI assistants, Compass creates **specialized agents** that understand domain-specific workflows.

### The Core Loop

```
Engineer → Prompt → Compass Agent → GUI Control → Engineering Software
                          ↑                              ↓
                          └──────── View & Monitor ──────┘
```

**Key Insight**: The agent doesn't just generate text—it **sees** the screen, **understands** the context, and **controls** the interface like a human engineer would.

---

## 🏗️ System Architecture

### 1. Frontend (Electron + React)

**Location**: `/frontend`

- **Main Process** (`frontend/main/`): Manages the Electron app lifecycle, window management, and IPC
- **Renderer Process** (`frontend/renderer/`):
  - **Main Chat** (`main-chat/`): Primary user interface for interacting with agents
  - **Template Training** (`template-training/`): AgentHub interface for training and managing agents
  - **App Context** (`common/context/AppContext.js`): Global state management using React Context

**Tech Stack**: Electron, React, WebSocket for real-time backend communication

---

### 2. Backend (Python + Flask-SocketIO)

**Location**: `/backend/src/compass`

#### Core Components:

##### a. **Agent System** (`agents/`)
- **Base Agent**: Foundation for all specialized agents
- **Tool Integration**: Connects agents to executable tools
- **Memory Management**: Short-term and long-term memory for context retention

##### b. **Computer Use Module** (`computer_use/`)
Controls the desktop environment:
- **Mouse Control**: Precise cursor movement and clicking
- **Keyboard Control**: Text input and keyboard shortcuts
- **Screen Monitoring**: Real-time screen capture and state tracking

##### c. **Vision System** (`vision/`)
**Object Detection in AgentHub**:
- Identifies UI elements (buttons, text fields, menus)
- Extracts text using OCR
- Recognizes software-specific components
- Enables visual grounding for actions

```python
# Example: Vision system identifies "Run Analysis" button
detected_objects = vision.detect_elements(screenshot)
# → [{"type": "button", "text": "Run Analysis", "bbox": [x, y, w, h]}]
```

##### d. **RAG System** (`database/`)
**Retrieval-Augmented Generation for domain knowledge**:
- **Vector Store** (ChromaDB): Stores software documentation embeddings
- **API Documentation**: Engineering software API references
- **Example Library**: Common workflow patterns
- **Retrieval**: Fetches relevant context for each user query

```python
# RAG in action
user_query = "How do I define load combinations in SAP2000?"
relevant_docs = rag.retrieve(user_query, top_k=5)
agent_response = llm.generate(query=user_query, context=relevant_docs)
```

##### e. **Tool System** (`tools/`)
Executable actions the agent can perform:
- **Software-Specific Tools**: API calls to engineering software
- **File Operations**: Reading/writing project files
- **Calculation Tools**: Engineering computations
- **Data Extraction**: Parse results and generate reports

---

## 🔄 End-to-End Workflow

### Training Phase (AgentHub)

```
1. Engineer selects target software (e.g., SAP2000)
2. Demonstrates workflows through the UI
3. Agent records:
   - Screen states (via computer vision)
   - Actions taken (mouse, keyboard)
   - Context (current model, active dialog)
4. RAG system ingests software documentation
5. Agent fine-tunes on demonstrated examples
6. Export trained agent as .agent file
```

**Key Technology**: 
- **Imitation Learning**: Agent learns from demonstrations
- **Computer Vision**: Object detection identifies UI elements
- **Action Space**: Mouse (x, y, click) + Keyboard (text, shortcuts)

---

### Execution Phase (Using Trained Agent)

```
1. User: "Create a steel frame with 5 bays"
2. Agent reasoning:
   a. RAG retrieves relevant documentation
   b. Breaks down task into steps
   c. Plans action sequence
3. Execution loop:
   a. Vision system captures screen
   b. Identifies current UI state
   c. Executes next action (click, type, etc.)
   d. Monitors result
   e. Adjusts if needed
4. Returns result to user
```

**Real Example**:
```
User: "Run modal analysis with 12 modes"

Agent Plan:
1. Click "Define" menu
2. Select "Analysis Cases"
3. Click "Add New Case"
4. Select "Modal" from dropdown
5. Enter "12" in "Number of Modes" field
6. Click "OK"
7. Click "Run" → "Run Analysis"
8. Monitor progress, report when complete
```

---

## 🧠 Key AI Components

### 1. Multi-Agent System

**Architecture**: Hierarchical agent structure
- **Orchestrator Agent**: Plans high-level workflow
- **Specialist Agents**: Execute domain-specific tasks
- **Tool Agents**: Handle software API calls

### 2. RAG (Retrieval-Augmented Generation)

**Why RAG?**
- Engineering software docs are too large for context windows
- Retrieves only relevant information per query
- Updates knowledge without retraining LLM

**Implementation**:
```python
# Vector store: Chroma
db = Chroma(persist_directory="./database/sap2000_api/")

# Embedding model: sentence-transformers
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Retrieval
docs = db.similarity_search(query, k=5)
```

### 3. Computer Vision for UI Understanding

**Object Detection**:
- Model: Custom YOLO fine-tuned on UI elements
- Detects: Buttons, text fields, dropdowns, dialogs, menus
- Enables: Visual grounding for actions

**Why Not Just API Calls?**
- Many engineering software lack complete APIs
- UI automation is more flexible
- Works with any software, even legacy

### 4. Action Space

**Low-Level Control**:
- Mouse: `move(x, y)`, `click()`, `drag(x1, y1, x2, y2)`
- Keyboard: `type(text)`, `press(key)`, `hotkey(ctrl, s)`

**High-Level Actions**:
- `open_file(path)`
- `run_analysis()`
- `export_results(format)`

---

## 📦 Project Structure

```
compass/
├── frontend/
│   ├── main/                    # Electron main process
│   ├── renderer/
│   │   ├── main-chat/          # Chat interface
│   │   ├── template-training/  # AgentHub UI
│   │   └── common/             # Shared components
│   └── dist/                   # Build output
│
├── backend/
│   └── src/compass/
│       ├── agents/             # Agent implementations
│       ├── computer_use/       # Desktop control (mouse/keyboard)
│       ├── vision/             # Object detection & OCR
│       ├── database/           # RAG system (ChromaDB)
│       ├── tools/              # Executable actions
│       └── app.py             # Flask-SocketIO server
│
├── docs/                       # GitHub Pages website (static)
├── training/                   # Sample trained agents
└── resources/                  # App assets (icons, etc.)
```

---

## 🔬 Learning Resources

### Concepts Used in Compass:

1. **Agentic AI**: Autonomous agents that plan and execute multi-step tasks
2. **RAG (Retrieval-Augmented Generation)**: Combining LLMs with external knowledge bases
3. **Computer Vision**: Object detection for UI understanding
4. **Desktop Automation**: Programmatic control of mouse, keyboard, screen
5. **Multi-Agent Systems**: Orchestration of specialized agents
6. **Imitation Learning**: Training agents from human demonstrations

### Key Technologies:

- **LangChain / LlamaIndex**: Agent frameworks
- **ChromaDB**: Vector database for RAG
- **OpenCV / YOLO**: Computer vision
- **PyAutoGUI**: Desktop automation
- **Flask-SocketIO**: Real-time communication
- **Electron**: Cross-platform desktop apps

---

## 🚀 Why This Architecture?

### Design Decisions:

1. **Desktop App (not web)**: 
   - Direct access to screen and input devices
   - No browser sandbox restrictions
   - Works offline after training

2. **Computer Vision + API**:
   - Vision: Works with any software
   - API: Faster, more reliable when available
   - Best of both worlds

3. **RAG over Fine-tuning**:
   - Documentation updates don't require retraining
   - Smaller model footprint
   - Transparent: shows which docs were used

4. **AgentHub (train once, share many)**:
   - Democratizes AI agent creation
   - One expert trains, thousands benefit
   - Community-driven knowledge

---

## 🎓 For Learners

This codebase demonstrates:
- ✅ Building production agentic AI systems
- ✅ Implementing RAG from scratch
- ✅ Computer vision for UI automation
- ✅ Multi-agent orchestration
- ✅ Real-time websocket architecture
- ✅ Electron + Python desktop apps

**Start Exploring**:
1. `backend/src/compass/agents/` - See how agents are structured
2. `backend/src/compass/database/` - RAG implementation
3. `backend/src/compass/computer_use/` - Desktop automation
4. `frontend/renderer/template-training/` - Agent training UI

---

## 📚 Further Reading

- [LangChain Documentation](https://python.langchain.com/)
- [RAG Explained](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [Agentic AI Patterns](https://github.com/microsoft/autogen)
- [Computer Vision for UI](https://github.com/ultralytics/ultralytics)

---

## 🤝 Contributing

We welcome contributions! See areas where you can help:
- Improve object detection accuracy
- Add support for new engineering software
- Optimize RAG retrieval
- Create better agent training workflows

---

**Questions?** Open an issue or discussion on GitHub!

Built with ❤️ for the engineering community

