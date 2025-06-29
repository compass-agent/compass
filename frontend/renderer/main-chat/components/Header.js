import { faSquare } from "@fortawesome/free-regular-svg-icons"
import {
  faCheck,
  faChevronDown,
  faMinus,
  faWindowMinimize,
  faXmark,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useState } from "react"
import { SAPConnectionStatus } from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import WebSocketService from "../../common/services/websocket"
import "../styles/Header.scss"

function Header() {
  const { state, dispatch } = useAppState()
  const { compassWindow, sap } = state

  // State for dropdowns and confirmation dialog
  const [agentDropdown, setAgentDropdown] = useState(false)
  const [toolsDropdown, setToolsDropdown] = useState(false)
  const [modelDropdown, setModelDropdown] = useState(false)
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [showAgentSelection, setShowAgentSelection] = useState(false)
  const [isInChat, setIsInChat] = useState(true) // Start as true so agent dropdown is read-only by default

  // Available options with descriptions
  const agentOptions = [
    { name: "Generic", description: "General purpose agent" },
    { name: "FreeCAD", description: "CAD design specialist" },
    { name: "OpenFoam", description: "Fluid dynamics expert" },
    { name: "structural-engineer", description: "Structural analysis expert" },
  ]
  const modelOptions = [
    {
      name: "Claude Sonnet 3.5",
      description: "Powerful reasoning and context",
    },
    { name: "OpenAI GPT-4o", description: "Great for most tasks" },
    { name: "Google Gemini 2.0", description: "Uses advanced reasoning" },
    {
      name: "DeepSeek R1",
      description: "Great at coding and visual reasoning",
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

  // Tool definitions with descriptions
  const toolOptions = [
    {
      name: "SAP",
      description: "Control SAP2000 on your behalf",
      status: getConnectionStatusColor(),
      isEnabled: true,
      isConnected: sap.connectionStatus === SAPConnectionStatus.CONNECTED,
      connectAction: handleConnectToSAP,
    },
    {
      name: "Desktop",
      description: "Control your screen, mouse and keyboard",
      status: "gray",
      isEnabled: false,
    },
    {
      name: "File Editor",
      description: "Access and edit project files",
      status: "gray",
      isEnabled: false,
    },
  ]

  const [selectedAgent, setSelectedAgent] = useState("structural-engineer")
  const [selectedModel, setSelectedModel] = useState("Claude Sonnet 3.5")

  // Helper function to format agent names for display
  const formatAgentName = (agentName) => {
    switch (agentName) {
      case "structural-engineer":
        return "Structural-Engineer"
      case "FreeCAD":
        return "FreeCAD"
      case "OpenFoam":
        return "OpenFoam"
      case "Generic":
        return "Generic"
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
    WebSocketService.connectToSAP()
  }

  // Open confirmation dialog before creating new chat
  const handleNewChatButtonClick = () => {
    setShowConfirmation(true)
  }

  // Cancel new chat action
  const handleCancelNewChat = () => {
    setShowConfirmation(false)
  }

  // Proceed to agent selection after confirmation
  const handleConfirmNewChat = () => {
    setShowConfirmation(false)
    setShowAgentSelection(true)
    setIsInChat(false) // Allow agent selection during new chat flow
  }

  // Cancel agent selection
  const handleCancelAgentSelection = () => {
    setShowAgentSelection(false)
    setIsInChat(true) // Return to read-only state
  }

  // Proceed with new chat after agent selection
  const handleFinalConfirmNewChat = (selectedAgent) => {
    setShowAgentSelection(false)
    setSelectedAgent(selectedAgent)
    setIsInChat(true) // Return to read-only state after selection
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
              src="../../../resources/compass.png"
              alt="Compass"
              style={{
                height: "25px",
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
              <div
                style={{
                  color: "#9C9B9F",
                  fontSize: "14px",
                  fontWeight: "400",
                  padding: "4px 0",
                }}
              >
                {formatAgentName(selectedAgent)}
              </div>
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
              className="header-tools-button"
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
                <div className="dropdown-header">Tools</div>
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
                          <div className="model-name">{tool.name}</div>
                          <div className="model-description">
                            {tool.description}
                          </div>
                        </div>
                      </div>
                    </div>
                    {tool.isEnabled ? (
                      <button
                        className="tool-button"
                        onClick={tool.connectAction}
                      >
                        {tool.isConnected ? "Reconnect" : "Connect"}
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
              className="header-model-button"
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
              <div className="header-dropdown-menu chatgpt-style">
                <div className="dropdown-header">Models</div>
                {modelOptions.map((model) => {
                  const isSelected = selectedModel === model.name
                  return (
                    <div
                      key={model.name}
                      className={`dropdown-item ${
                        isSelected ? "selected" : ""
                      }`}
                      onClick={() => handleModelSelect(model.name)}
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
                          <div className="model-name">{model.name}</div>
                          <div className="model-description">
                            {model.description}
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
                <div className="dropdown-footer">More models</div>
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
            marginRight: "6px",
          }}
        >
          <button
            className="header-new-chat-button"
            onClick={handleNewChatButtonClick}
            title="New Chat"
          >
            New Chat
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
      {showAgentSelection && (
        <div className="confirmation-overlay">
          <div
            className="confirmation-dialog"
            style={{ width: "280px", maxWidth: "90vw" }}
          >
            <div className="confirmation-content">
              <h3 style={{ marginBottom: "6px", fontSize: "16px" }}>
                Select Agent Type
              </h3>
              <p style={{ marginBottom: "12px", fontSize: "13px" }}>
                Choose the type of agent for your new chat session.
              </p>
              <div className="agent-selection-grid">
                {agentOptions.map((agent) => (
                  <div
                    key={agent.name}
                    className="agent-option-card"
                    onClick={() => handleFinalConfirmNewChat(agent.name)}
                    style={{
                      padding: "8px 12px",
                      border: "1px solid #3D3D3D",
                      borderRadius: "4px",
                      cursor: "pointer",
                      marginBottom: "4px",
                      backgroundColor:
                        selectedAgent === agent.name ? "#4A4A4A" : "#2D2D2D",
                      transition: "background-color 0.2s ease",
                    }}
                    onMouseEnter={(e) => {
                      if (selectedAgent !== agent.name) {
                        e.currentTarget.style.backgroundColor = "#3A3A3A"
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedAgent !== agent.name) {
                        e.currentTarget.style.backgroundColor = "#2D2D2D"
                      }
                    }}
                  >
                    <div
                      style={{
                        fontWeight: "500",
                        marginBottom: "1px",
                        color: "#E0E0E0",
                        fontSize: "13px",
                      }}
                    >
                      {formatAgentName(agent.name)}
                    </div>
                    <div style={{ fontSize: "11px", color: "#9C9B9F" }}>
                      {agent.description}
                    </div>
                  </div>
                ))}
              </div>
              <div
                className="confirmation-buttons"
                style={{ marginTop: "12px" }}
              >
                <button
                  className="cancel-button"
                  onClick={handleCancelAgentSelection}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Header
