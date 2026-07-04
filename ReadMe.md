<p align="center">
  <img src="docs/images/logo/compass-mark.png" width="88" alt="Compass logo">
</p>

<h1 align="center">Compass</h1>

<p align="center">
  <b>AI operators for professional desktop software.</b><br>
  Compass is an open-source Windows desktop agent for GUI-heavy engineering tools,<br>
  starting with CSI SAP2000.
</p>

<p align="center">
  <a href="https://compass-agent.github.io/compass">Website</a> |
  <a href="https://github.com/compass-agent/compass/releases">Download</a> |
  <a href="https://compass-agent.github.io/compass#sap2000">Demo</a> |
  <a href="./ARCHITECTURE.md">Architecture</a>
</p>

---

## What Compass Is

Compass is a Windows desktop AI agent that operates professional software the way a
human operator does: it can look at the screen, reason about the UI, and drive the
mouse and keyboard. When the target application exposes a better automation path,
Compass uses that too. For SAP2000, the agent combines computer use with the
SAP2000 COM/API interface.

The goal is not just one SAP2000 chatbot. The broader Compass architecture is a
general harness for GUI-heavy professional software:

- Screen grounding from screenshots, detected UI controls, OCR, captions, and coordinates.
- Hybrid control through mouse/keyboard plus native APIs, scripting, or COM.
- Retrieved documentation and software-specific prompt scaffolding.
- Human-taught UI templates and workflow examples.
- AgentHub for creating, importing, exporting, and sharing specialized agents.
- Manual, semi-automatic, and automatic execution modes.

## Current Vertical: SAP2000

The current public build focuses on CSI SAP2000 as the first complete vertical.
Compass can connect to an already-open SAP2000 session, query model state, create
and edit model objects, generate API-grounded scripts, and support longer
structural-engineering workflows.

## Quick Start

1. Download the latest installer from [Releases](https://github.com/compass-agent/compass/releases).
2. Run `Compass-Setup-<version>.exe`.
3. On first launch, add your [Anthropic API key](https://console.anthropic.com).
4. Open SAP2000.
5. In Compass, use `Tools -> SAP2000 Scripting -> Connect`.

Requirements:

- Windows 10 or 11, 64-bit.
- CSI SAP2000 installed and licensed.
- Anthropic API key for the current public agent model.
- Optional OpenAI key for semantic search over SAP2000 documentation.

Tip: run Compass and SAP2000 at the same Windows privilege level. If one process
is running as Administrator and the other is not, Windows can block COM attach to
the existing SAP2000 session.

## Develop

Prerequisites:

- [Node.js](https://nodejs.org/) >= 16
- [Python](https://python.org/downloads/) >= 3.11
- Windows for SAP2000/COM integration

```bash
# First-time setup. Creates .venv and installs Python + Node dependencies.
npm run setup

# Daily development. Starts backend, renderer watch, and Electron together.
npm run dev
```

API keys are managed in the app settings and stored in
`%APPDATA%\Compass\settings.json`. Environment variables such as
`ANTHROPIC_API_KEY` take precedence when set.

## Build the Windows Installer

```bash
npm run dist:win
# Produces dist/Compass-Setup-<version>.exe
```

The build runs PyInstaller for the Python backend, webpack for the renderer, and
electron-builder for the Windows installer.

See [RELEASING.md](./RELEASING.md) for the release process.

## Architecture

Compass uses an Electron shell with a React renderer and a Python Flask-SocketIO
backend. The backend hosts the LLM agent loop, the SAP2000 COM integration, the
screen/perception tooling, the Chroma-backed SAP2000 API knowledge base, and the
AgentHub training/import/export flows. The frontend and backend communicate over
Socket.IO on localhost.

Details are in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Trust Model

Compass is local-first and open source. It does not require a Compass cloud
account or proxy server. Model requests are made from your machine using provider
credentials you control, so review the data policies of the model providers you
configure for your workflows.

## Contributing

Contributions are welcome. Please open an
[issue](https://github.com/compass-agent/compass/issues) to discuss significant
changes first.

## License

[MIT](./LICENSE)
