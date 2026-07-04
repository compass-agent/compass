import { faSquare } from "@fortawesome/free-regular-svg-icons"
import {
  faCheck,
  faChevronDown,
  faGear,
  faInfoCircle,
  faMinus,
  faWindowMinimize,
  faXmark,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useState } from "react"
import {
  DesktopConnectionStatus,
  ActionTypes,
  SAPConnectionStatus,
} from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import WebSocketService from "../../common/services/websocket"
import "../styles/Header.scss"

// Tooltip component for tools dropdown
const ToolTooltip = ({ text, children }) => {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className="tool-tooltip-container">
      <div
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {children}
      </div>
      {showTooltip && <div className="tool-tooltip-content">{text}</div>}
    </div>
  )
}

const DEFAULT_AGENT_DATA = {
  name: "structural-engineer",
  description: "Structural engineering assistant with SAP2000 integration",
  generalTools: [],
  softwareIntegrations: [
    {
      id: "SAP2000",
      name: "SAP2000",
      scripting: true,
      desktop: false,
      config: {},
    },
  ],
  configuration: {},
}

function Header() {
  const { state, dispatch } = useAppState()
  const { compassWindow, sap, desktop } = state

  // State for dropdowns and confirmation dialog
  const [agentDropdown, setAgentDropdown] = useState(false)
  const [toolsDropdown, setToolsDropdown] = useState(false)
  const [modelDropdown, setModelDropdown] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [isInChat, setIsInChat] = useState(true) // Start as true so agent dropdown is read-only by default
  const [thinkingModeEnabled, setThinkingModeEnabled] = useState(true) // Thinking mode enabled by default

  const [selectedAgent, setSelectedAgent] = useState(DEFAULT_AGENT_DATA.name)
  const [selectedModel, setSelectedModel] = useState("Claude Sonnet 4.5")
  const [selectedAgentData, setSelectedAgentData] = useState(DEFAULT_AGENT_DATA)

  // Load last selected agent on startup
  useEffect(() => {
    const loadLastAgent = async () => {
      if (window.electron?.ipcRenderer?.invoke) {
        try {
          const lastAgent = await window.electron.ipcRenderer.invoke(
            "load-last-agent"
          )
          if (lastAgent && (lastAgent.name || lastAgent.agentId)) {
            console.log("🎯 Loading last selected agent:", lastAgent)
            setSelectedAgent(lastAgent.name || "Unknown Agent")
            setSelectedAgentData(lastAgent)
          }
        } catch (error) {
          console.log("🎯 Could not load last agent:", error.message)
        }
      }
    }

    loadLastAgent()
  }, [])

  // Listen for agent selection from template training window
  useEffect(() => {
    if (window.electron?.ipcRenderer?.on) {
      const handleAgentUpdate = (agentData) => {
        console.log("🎯 Received agent update in main window:", agentData)
        console.log("🎯 Type of received data:", typeof agentData)
        console.log("🎯 Is array:", Array.isArray(agentData))
        console.log(
          "🎯 Object keys:",
          agentData ? Object.keys(agentData) : "no keys"
        )
        console.log("🎯 Raw agent data:", agentData)

        // Try to access properties directly
        if (agentData) {
          console.log("🎯 Direct access - name:", agentData.name)
          console.log("🎯 Direct access - agentId:", agentData.agentId)
          console.log("🎯 Direct access - tools:", agentData.tools)
          console.log("🎯 Direct access - targetApp:", agentData.targetApp)
          console.log("🎯 Direct access - description:", agentData.description)
        }

        console.log(
          "🎯 Full agent data structure:",
          JSON.stringify(agentData, null, 2)
        )

        if (agentData && (agentData.name || agentData.agentId)) {
          setSelectedAgent(agentData.name || "Unknown Agent")
          setSelectedAgentData(agentData)
          console.log("🎯 Updated selectedAgentData to:", agentData)
          console.log("🎯 Tools in updated data:", agentData.tools)
        } else {
          console.error("🎯 Invalid agent data received:", agentData)
        }
      }

      window.electron.ipcRenderer.on("update-selected-agent", handleAgentUpdate)

      return () => {
        if (window.electron?.ipcRenderer?.removeListener) {
          window.electron.ipcRenderer.removeListener(
            "update-selected-agent",
            handleAgentUpdate
          )
        }
      }
    }
  }, [])

  // Available options with descriptions
  const agentOptions = [
    {
      name: "structural-engineer",
      description: "SAP2000 structural engineering assistant",
    },
    { name: "Generic", description: "General purpose agent" },
    { name: "FreeCAD", description: "CAD design specialist" },
    { name: "OpenFoam", description: "Fluid dynamics expert" },
  ]
  const modelOptions = [
    {
      name: "Claude Sonnet 4.5",
      description:
        "Advanced reasoning with extended thinking capabilities, excels at complex analysis and problem-solving with enhanced emotional intelligence",
      enabled: true,
    },
    {
      name: "OpenAI GPT-5",
      description:
        "Next-generation model with unified architecture, combining powerful reasoning and multimodal processing for sophisticated AI interactions",
      enabled: false,
    },
    {
      name: "Google Gemini 2.5",
      description:
        "Price-performance champion with configurable thinking budgets, multimodal processing, and cost-efficient deployment at scale",
      enabled: false,
    },
  ]

  // Helper function for getting connection status color
  const getConnectionStatusColor = () => {
    switch (sap.connectionStatus) {
      case SAPConnectionStatus.CONNECTED:
        return "green"
      case SAPConnectionStatus.CONNECTING:
        return "orange"
      case SAPConnectionStatus.DISCONNECTED:
        return "red"
      default:
        return "gray"
    }
  }

  // Helper function for getting desktop connection status color
  const getDesktopConnectionStatusColor = () => {
    switch (desktop.connectionStatus) {
      case DesktopConnectionStatus.CONNECTED:
        return "green"
      case DesktopConnectionStatus.CONNECTING:
        return "orange"
      case DesktopConnectionStatus.DISCONNECTED:
        return "red"
      default:
        return "gray"
    }
  }

  // Tool definitions with descriptions - filtered based on selected agent
  const getToolOptions = () => {
    console.log(
      "🔧 getToolOptions called with selectedAgentData:",
      selectedAgentData
    )

    const allTools = []

    // Add software integrations (SAP2000, OpenFOAM, FreeCAD, etc.)
    selectedAgentData?.softwareIntegrations?.forEach((integration) => {
      // Add scripting tool for the software
      switch (integration.id) {
        case "SAP2000":
          if (integration.scripting) {
            allTools.push({
              name: "SAP2000 Scripting",
              description: "Control SAP2000 through scripting",
              status: getConnectionStatusColor(),
              isEnabled: true,
              isConnected:
                sap.connectionStatus === SAPConnectionStatus.CONNECTED,
              isConnecting:
                sap.connectionStatus === SAPConnectionStatus.CONNECTING,
              message: sap.message,
              connectAction: handleConnectToSAP,
              toolKey: "sap",
            })
          }
          break
        case "OpenFOAM":
          if (integration.scripting) {
            allTools.push({
              name: "OpenFOAM",
              description: "Connect to OpenFOAM for CFD simulations",
              status: "gray",
              isEnabled: true,
              isConnected: false,
              connectAction: () =>
                console.log("OpenFOAM connection not implemented yet"),
              toolKey: "openfoam",
            })
          }
          break
        case "FreeCAD":
          if (integration.scripting) {
            allTools.push({
              name: "FreeCAD",
              description: "Connect to FreeCAD for 3D modeling",
              status: "gray",
              isEnabled: true,
              isConnected: false,
              connectAction: () =>
                console.log("FreeCAD connection not implemented yet"),
              toolKey: "freecad",
            })
          }
          break
      }

      // Add desktop UI tool if enabled for this software
      if (integration.desktop) {
        allTools.push({
          name: "SAP2000 UI Interaction",
          description: `Control ${
            integration.name || integration.id
          } through desktop interface`,
          status: getDesktopConnectionStatusColor(),
          isEnabled: true,
          isConnected:
            desktop.connectionStatus === DesktopConnectionStatus.CONNECTED,
          connectAction: handleConnectToDesktop,
          toolKey: "desktop",
        })
      }
    })

    // Add general tools (file editor, command line, etc.)
    selectedAgentData?.generalTools?.forEach((tool) => {
      switch (tool.id) {
        case "fileEditor":
          allTools.push({
            name: "File Editor",
            description: "Access and edit project files",
            status: "gray",
            isEnabled: true,
            toolKey: "fileEditor",
          })
          break
        case "commandLine":
          allTools.push({
            name: "Command Line",
            description: "Execute command line operations",
            status: "gray",
            isEnabled: true,
            toolKey: "commandLine",
          })
          break
      }
    })

    console.log(
      "🔧 Built tools dynamically:",
      allTools.map((t) => t.name)
    )
    return allTools
  }

  const toolOptions = getToolOptions()

  // Helper function to format agent names for display
  const formatAgentName = (agentName) => {
    if (!agentName) {
      return "No Agent Selected"
    }
    switch (agentName) {
      case "FreeCAD":
        return "FreeCAD"
      case "OpenFoam":
        return "OpenFoam"
      case "Generic":
        return "Generic"
      case "structural-engineer":
        return "Structural Engineer"
      default:
        return agentName
    }
  }

  let isMac = window.electron.platform === "darwin"
  const isWindows = window.electron.platform === "win32"

  // Close all dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      // Check if click is on an actual dropdown menu
      const isInsideDropdownMenu = event.target.closest(".header-dropdown-menu")
      // Check if click is on a dropdown button
      const isDropdownButton = event.target.closest(".header-dropdown-button")
      // Check if click is on header areas
      const isOnHeader = event.target.closest(".header-container")

      // Close dropdowns if:
      // 1. Clicking outside dropdown menus AND not on dropdown buttons
      // 2. OR clicking on header areas (but not dropdown buttons or menus)
      if (
        (!isInsideDropdownMenu && !isDropdownButton) ||
        (isOnHeader && !isInsideDropdownMenu && !isDropdownButton)
      ) {
        setAgentDropdown(false)
        setToolsDropdown(false)
        setModelDropdown(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  // SAP Connection handlers
  function handleConnectToSAP(e) {
    if (e) e.stopPropagation() // Prevent dropdown from closing
    console.log("Connect to SAP button clicked")
    dispatch({
      type: ActionTypes.SET_SAP_CONNECTION_STATUS,
      payload: {
        status: SAPConnectionStatus.CONNECTING,
        message: "Connecting to SAP2000...",
      },
    })
    WebSocketService.connectToSAP()
  }

  // Desktop Connection handlers
  function handleConnectToDesktop(e) {
    if (e) e.stopPropagation() // Prevent dropdown from closing
    console.log("Connect to Desktop button clicked")
    WebSocketService.connectToDesktop()
  }

  // Open Template Training window
  const handleOpenTemplateTraining = () => {
    if (window.electron?.ipcRenderer?.send) {
      window.electron.ipcRenderer.send("open-template-training")
    }
  }

  // Open confirmation dialog before creating new chat
  const handleNewChatButtonClick = () => {
    setShowConfirmation(true)
  }

  // Cancel new chat action
  const handleCancelNewChat = () => {
    setShowConfirmation(false)
  }

  // Proceed directly with new chat using current agent (no selection dialog)
  const handleConfirmNewChat = () => {
    setShowConfirmation(false)
    WebSocketService.handleNewChat(selectedAgent)
  }

  const handleClose = () => {
    if (window.electron && window.electron.closeWindow) {
      window.electron.closeWindow()
    }
  }

  const handleMinimize = () => {
    window.electron.minimizeWindow()
  }

  const handleToggleMaximizeWindow = () => {
    if (window.electron?.toggleMaximizeWindow) {
      window.electron.toggleMaximizeWindow()
    }
  }

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent)
    setAgentDropdown(false)
  }

  const handleModelSelect = (model) => {
    setSelectedModel(model)
    setModelDropdown(false)
  }

  // Handle dropdown toggle with stopPropagation
  const toggleDropdown = (dropdown, setDropdown, e) => {
    e.stopPropagation()
    // Close other dropdowns
    if (dropdown === "agent") {
      setToolsDropdown(false)
      setModelDropdown(false)
    } else if (dropdown === "tools") {
      setAgentDropdown(false)
      setModelDropdown(false)
    } else if (dropdown === "model") {
      setAgentDropdown(false)
      setToolsDropdown(false)
    }
    setDropdown((prev) => !prev)
  }

  return (
    <div className="header-container">
      {/* Top level header - App name and window controls */}
      <div
        className={`top-header ${isMac ? "macos" : "windows"}`}
        style={{
          WebkitAppRegion: "drag",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          width: "100%",
        }}
      >
        {/* Left side: Compass logo and Agent dropdown */}
        <div
          className="left-header-controls"
          style={{
            WebkitAppRegion: "no-drag",
            display: "flex",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <div
            className="app-name"
            style={{
              display: "flex",
              alignItems: "center",
              height: "25px",
            }}
          >
            <img
              src="../assets/compass.png"
              alt="Compass"
              style={{
                height: "22px",
                width: "auto",
              }}
            />
          </div>

          {/* Agent Display - Read-only during chat, dropdown when not in chat */}
          <div className="header-dropdown-container">
            {!isInChat ? (
              <button
                className="header-dropdown-button"
                onClick={(e) => toggleDropdown("agent", setAgentDropdown, e)}
                style={{
                  background: "none",
                  border: "none",
                  color: "#9C9B9F",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  padding: "4px 0",
                  fontSize: "13px",
                  fontWeight: "400",
                }}
              >
                <span>{formatAgentName(selectedAgent)}</span>
                <FontAwesomeIcon
                  icon={faChevronDown}
                  className="dropdown-arrow"
                  style={{
                    fontSize: "12px",
                    color: "#6A6A6A",
                    marginLeft: "8px",
                  }}
                />
              </button>
            ) : (
              <button
                className="agent-text clickable-agent"
                onClick={handleOpenTemplateTraining}
                style={{
                  color: "#9C9B9F",
                  fontSize: "15px",
                  fontWeight: "400",
                  padding: "4px 0",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                }}
                title="Click to open Agent Hub"
              >
                {formatAgentName(selectedAgent)}
                <span
                  style={{
                    marginLeft: "6px",
                    fontSize: "12px",
                    color: "#6A6A6A",
                    opacity: 0.7,
                  }}
                >
                  ⚙️
                </span>
              </button>
            )}

            {agentDropdown && !isInChat && (
              <>
                {/* Backdrop to prevent background clicks */}
                <div
                  style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    zIndex: 9998,
                    backgroundColor: "transparent",
                  }}
                  onClick={() => setAgentDropdown(false)}
                />
                <div
                  className="header-dropdown-menu chatgpt-style"
                  style={{
                    zIndex: 9999,
                    backgroundColor: "#2D2D2D",
                    border: "1px solid #3D3D3D",
                    borderRadius: "8px",
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
                    position: "absolute",
                    minWidth: "200px",
                    maxWidth: "250px",
                    width: "max-content",
                  }}
                >
                  {agentOptions.map((agent) => {
                    const isSelected = selectedAgent === agent.name
                    return (
                      <div
                        key={agent.name}
                        className={`dropdown-item ${
                          isSelected ? "selected" : ""
                        }`}
                        onClick={() => handleAgentSelect(agent.name)}
                        style={
                          isSelected
                            ? {
                                backgroundColor: "#4A4A4A",
                                width: "100%",
                                boxSizing: "border-box",
                              }
                            : {
                                width: "100%",
                                boxSizing: "border-box",
                              }
                        }
                      >
                        <div className="dropdown-item-content">
                          <div className="model-info">
                            <div className="model-name">{agent.name}</div>
                            <div className="model-description">
                              {agent.description}
                            </div>
                          </div>
                          {isSelected && (
                            <FontAwesomeIcon
                              icon={faCheck}
                              className="selected-icon"
                              style={{ color: "#E0E0E0" }}
                            />
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Window Controls: Left for macOS, Right for Windows */}
        <div
          className={`window-controls ${
            isMac ? "left macos" : "right windows"
          }`}
          style={{ WebkitAppRegion: "no-drag" }}
        >
          {isMac ? (
            <>
              <button
                className="window-control macos close"
                onClick={handleClose}
                style={{ color: "#9C9B9F" }}
              >
                <FontAwesomeIcon icon={faXmark} />
              </button>
              <button
                className="window-control macos min"
                onClick={handleMinimize}
                style={{ color: "#9C9B9F" }}
              >
                <FontAwesomeIcon icon={faMinus} />
              </button>
              <button
                className="window-control macos max"
                onClick={handleToggleMaximizeWindow}
                style={{ color: "#9C9B9F" }}
              >
                <FontAwesomeIcon icon={faSquare} />
              </button>
            </>
          ) : (
            <>
              <button
                className="window-control minimize win"
                onClick={handleMinimize}
                style={{ color: "#9C9B9F" }}
              >
                <FontAwesomeIcon icon={faWindowMinimize} />
              </button>
              <button
                className="window-control win"
                onClick={handleToggleMaximizeWindow}
                style={{ color: "#9C9B9F" }}
              >
                <FontAwesomeIcon icon={faSquare} />
              </button>
              <button
                className="window-control win"
                onClick={handleClose}
                style={{ color: "#9C9B9F" }}
              >
                <FontAwesomeIcon icon={faXmark} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Second level header - Main controls */}
      <div
        className="main-header"
        style={{ WebkitAppRegion: "drag", backgroundColor: "transparent" }}
      >
        <div
          className="main-header-controls"
          style={{ WebkitAppRegion: "no-drag" }}
        >
          {/* Tools Dropdown */}
          <div className="header-dropdown-container">
            <button
              className={`header-tools-button ${toolsDropdown ? "active" : ""}`}
              onClick={(e) => toggleDropdown("tools", setToolsDropdown, e)}
            >
              Tools
              <FontAwesomeIcon
                icon={faChevronDown}
                style={{
                  fontSize: "10px",
                  marginLeft: "6px",
                  color: "#6A6A6A",
                }}
              />
            </button>

            {toolsDropdown && (
              <div className="header-dropdown-menu chatgpt-style tools-menu">
                {toolOptions.map((tool) => (
                  <div key={tool.name} className="tool-item">
                    <div className="tool-info">
                      <div className="tool-status">
                        <div
                          className="status-indicator"
                          style={{
                            backgroundColor: tool.status,
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            display: "inline-block",
                            position: "relative",
                            zIndex: 10,
                            marginRight: "8px",
                            flexShrink: 0,
                            minWidth: "8px",
                            minHeight: "8px",
                          }}
                        ></div>
                        <div className="model-info">
                          <div className="model-name">
                            {tool.name}
                            <ToolTooltip text={tool.description}>
                              <FontAwesomeIcon
                                icon={faInfoCircle}
                                className="tool-info-icon"
                              />
                            </ToolTooltip>
                          </div>
                          {tool.message && (
                            <div className="tool-message" title={tool.message}>
                              {tool.message}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    {tool.isEnabled ? (
                      <button
                        className={`tool-button ${tool.isConnected ? "connected" : ""} ${
                          tool.isConnecting ? "disabled" : ""
                        }`}
                        onClick={tool.connectAction}
                        disabled={tool.isConnecting}
                      >
                        {tool.isConnecting
                          ? "Connecting..."
                          : tool.isConnected
                          ? "Reconnect"
                          : "Connect"}
                      </button>
                    ) : (
                      <button className="tool-button disabled">Connect</button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Model Dropdown */}
          <div className="header-dropdown-container">
            <button
              className={`header-model-button ${modelDropdown ? "active" : ""}`}
              onClick={(e) => toggleDropdown("model", setModelDropdown, e)}
            >
              Model
              <FontAwesomeIcon
                icon={faChevronDown}
                style={{
                  fontSize: "10px",
                  marginLeft: "6px",
                  color: "#6A6A6A",
                }}
              />
            </button>

            {modelDropdown && (
              <div className="header-dropdown-menu chatgpt-style models-menu">
                {modelOptions.map((model) => {
                  const isSelected = selectedModel === model.name
                  const isDisabled = !model.enabled
                  return (
                    <div
                      key={model.name}
                      className={`tool-item ${isSelected ? "selected" : ""} ${isDisabled ? "disabled" : ""}`}
                      onClick={() => model.enabled && handleModelSelect(model.name)}
                    >
                      <div className="tool-info">
                        <div className="tool-status">
                          <div className="model-info">
                            <div className="model-name">
                              {model.name}
                              <ToolTooltip text={model.description}>
                                <FontAwesomeIcon
                                  icon={faInfoCircle}
                                  className="tool-info-icon"
                                />
                              </ToolTooltip>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
                <div className="dropdown-footer">
                  <div
                    className="thinking-toggle"
                    onClick={() => setThinkingModeEnabled(!thinkingModeEnabled)}
                  >
                    <span>Thinking Mode</span>
                    <div
                      className={`toggle-switch ${
                        thinkingModeEnabled ? "enabled" : "disabled"
                      }`}
                    >
                      <div className="toggle-slider"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* New Chat Button (moved to right side) */}
        <div
          className="right-controls"
          style={{
            WebkitAppRegion: "no-drag",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            marginRight: "12px",
          }}
        >
          {/* Training button removed as per refactor */}
          <button
            className="header-new-chat-button"
            onClick={handleNewChatButtonClick}
            title="New Chat"
          >
            New Chat
          </button>
          <button
            className="header-settings-button"
            onClick={() =>
              window.dispatchEvent(new CustomEvent("open-compass-settings"))
            }
            title="Settings (API keys)"
            style={{
              background: "none",
              border: "none",
              color: "#9C9B9F",
              cursor: "pointer",
              fontSize: "14px",
              padding: "4px 6px",
            }}
          >
            <FontAwesomeIcon icon={faGear} />
          </button>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmation && (
        <div className="confirmation-overlay">
          <div className="confirmation-dialog">
            <div className="confirmation-content">
              <h3>Start a new chat?</h3>
              <p>
                This will archive and deactivate your current session. You can
                still access it later from your history.
              </p>
              <div className="confirmation-buttons">
                <button className="cancel-button" onClick={handleCancelNewChat}>
                  Cancel
                </button>
                <button
                  className="confirm-button"
                  onClick={handleConfirmNewChat}
                >
                  Start new chat
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent Selection Dialog */}
      {/* This section is removed as per the edit hint */}
    </div>
  )
}

export default Header
