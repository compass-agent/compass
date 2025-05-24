import React, { useState, useEffect } from "react";
import { useAppState } from "../../common/context/AppContext";
import "../styles/Header.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faXmark,
  faWindowMinimize,
  faMinus,
  faPlug,
  faSquare,
  faChevronDown,
  faPlus,
  faCheck,
  faDesktop,
  faFileAlt
} from "@fortawesome/free-solid-svg-icons";
import WebSocketService from "../../common/services/websocket";
import { SAPConnectionStatus } from "../../common/constants";

function Header() {
  const { state, dispatch } = useAppState();
  const { compassWindow, sap } = state;
  
  // State for dropdowns
  const [agentDropdown, setAgentDropdown] = useState(false);
  const [toolsDropdown, setToolsDropdown] = useState(false);
  const [modelDropdown, setModelDropdown] = useState(false);
  
  // Available options with descriptions
  const agentOptions = [
    { name: "Generic", description: "General purpose agent" },
    { name: "FreeCAD", description: "CAD design specialist" },
    { name: "OpenFoam", description: "Fluid dynamics expert" },
    { name: "structural-engineer", description: "Structural analysis expert" }
  ];
  const modelOptions = [
    { name: "Claude Sonnet 3.5", description: "Powerful reasoning and context" },
    { name: "OpenAI GPT-4o", description: "Great for most tasks" },
    { name: "Google Gemini 2.0", description: "Uses advanced reasoning" },
    { name: "DeepSeek R1", description: "Great at coding and visual reasoning" }
  ];
  
  // Helper function for getting connection status color
  const getConnectionStatusColor = () => {
    switch (sap.connectionStatus) {
      case SAPConnectionStatus.CONNECTED:
        return "green";
      case SAPConnectionStatus.CONNECTING:
        return "orange";
      case SAPConnectionStatus.DISCONNECTED:
        return "red";
      default:
        return "gray";
    }
  };
  
  // Tool definitions with descriptions
  const toolOptions = [
    { 
      name: "SAP", 
      description: "Control SAP2000 on your behalf", 
      status: getConnectionStatusColor(),
      isEnabled: true,
      isConnected: sap.connectionStatus === SAPConnectionStatus.CONNECTED,
      connectAction: handleConnectToSAP 
    },
    { 
      name: "Desktop", 
      description: "Control your screen, mouse and keyboard",
      status: "gray",
      isEnabled: false
    },
    { 
      name: "File Editor", 
      description: "Access and edit project files",
      status: "gray",
      isEnabled: false
    }
  ];
  
  const [selectedAgent, setSelectedAgent] = useState("structural-engineer");
  const [selectedModel, setSelectedModel] = useState("Claude Sonnet 3.5");

  let isMac = window.electron.platform === "darwin";
  const isWindows = window.electron.platform === "win32";

  // Close all dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setAgentDropdown(false);
      setToolsDropdown(false);
      setModelDropdown(false);
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  // SAP Connection handlers
  function handleConnectToSAP(e) {
    if (e) e.stopPropagation(); // Prevent dropdown from closing
    console.log("Connect to SAP button clicked");
    WebSocketService.connectToSAP();
  }
  
  const handleNewChat = () => {
    WebSocketService.handleNewChat(selectedAgent);
  };

  const handleClose = () => {
    if (window.electron && window.electron.closeWindow) {
      window.electron.closeWindow();
    }
  };

  const handleMinimize = () => {
    window.electron.minimizeWindow();
  };

  const handleToggleMaximizeWindow = () => {
    if (window.electron?.toggleMaximizeWindow) {
      window.electron.toggleMaximizeWindow();
    }
  };

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent);
    setAgentDropdown(false);
  };

  const handleModelSelect = (model) => {
    setSelectedModel(model);
    setModelDropdown(false);
  };

  // Handle dropdown toggle with stopPropagation
  const toggleDropdown = (dropdown, setDropdown, e) => {
    e.stopPropagation();
    // Close other dropdowns
    if (dropdown === 'agent') {
      setToolsDropdown(false);
      setModelDropdown(false);
    } else if (dropdown === 'tools') {
      setAgentDropdown(false);
      setModelDropdown(false);
    } else if (dropdown === 'model') {
      setAgentDropdown(false);
      setToolsDropdown(false);
    }
    setDropdown(prev => !prev);
  };

  return (
    <div className="header-container">
      {/* Top level header - App name and window controls */}
      <div className={`top-header ${isMac ? "macos" : "windows"}`}>
        <div className="app-name">Compass</div>
        
        {/* Window Controls: Left for macOS, Right for Windows */}
        {isMac ? (
          <div className="window-controls left macos">
            <button className="window-control macos close" onClick={handleClose}>
              <FontAwesomeIcon icon={faXmark} />
            </button>
            <button className="window-control macos min" onClick={handleMinimize}>
              <FontAwesomeIcon icon={faMinus} />
            </button>
            <button className="window-control macos max" onClick={handleToggleMaximizeWindow}>
              <FontAwesomeIcon icon={faSquare} />
            </button>
          </div>
        ) : (
          <div className="window-controls right">
            <button className="window-control minimize win" onClick={handleMinimize}>
              <FontAwesomeIcon icon={faWindowMinimize} />
            </button>
            <button className="window-control win" onClick={handleToggleMaximizeWindow}>
              <FontAwesomeIcon icon={faSquare} />
            </button>
            <button className="window-control win" onClick={handleClose}>
              <FontAwesomeIcon icon={faXmark} />
            </button>
          </div>
        )}
      </div>
      
      {/* Second level header - Main controls */}
      <div className="main-header">
        <div className="main-header-controls">
          {/* Agent Dropdown */}
          <div className="header-dropdown-container">
            <button 
              className="header-dropdown-button" 
              onClick={(e) => toggleDropdown('agent', setAgentDropdown, e)}
            >
              <span>Agent</span>
              <FontAwesomeIcon icon={faChevronDown} className="dropdown-arrow" />
            </button>
            
            {agentDropdown && (
              <div className="header-dropdown-menu chatgpt-style">
                {agentOptions.map((agent) => {
                  const isSelected = selectedAgent === agent.name;
                  return (
                    <div 
                      key={agent.name} 
                      className={`dropdown-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleAgentSelect(agent.name)}
                    >
                      <div className="dropdown-item-content">
                        <div className="model-info">
                          <div className="model-name">{agent.name}</div>
                          <div className="model-description">{agent.description}</div>
                        </div>
                        {isSelected && (
                          <FontAwesomeIcon icon={faCheck} className="selected-icon" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          
          <div className="header-separator"></div>
          
          {/* Tools Dropdown */}
          <div className="header-dropdown-container">
            <button 
              className="header-dropdown-button" 
              onClick={(e) => toggleDropdown('tools', setToolsDropdown, e)}
            >
              <span>Tools</span>
              <FontAwesomeIcon icon={faChevronDown} className="dropdown-arrow" />
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
                          style={{ backgroundColor: tool.status }}
                        ></div>
                        <div className="model-info">
                          <div className="model-name">{tool.name}</div>
                          <div className="model-description">{tool.description}</div>
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
                      <button className="tool-button disabled">
                        Connect
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="header-separator"></div>
          
          {/* AI Model Dropdown */}
          <div className="header-dropdown-container">
            <button 
              className="header-dropdown-button" 
              onClick={(e) => toggleDropdown('model', setModelDropdown, e)}
            >
              <span>Model</span>
              <FontAwesomeIcon icon={faChevronDown} className="dropdown-arrow" />
            </button>
            
            {modelDropdown && (
              <div className="header-dropdown-menu chatgpt-style">
                <div className="dropdown-header">Models</div>
                {modelOptions.map((model) => {
                  const isSelected = selectedModel === model.name;
                  return (
                    <div 
                      key={model.name} 
                      className={`dropdown-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleModelSelect(model.name)}
                    >
                      <div className="dropdown-item-content">
                        <div className="model-info">
                          <div className="model-name">{model.name}</div>
                          <div className="model-description">{model.description}</div>
                        </div>
                        {isSelected && (
                          <FontAwesomeIcon icon={faCheck} className="selected-icon" />
                        )}
                      </div>
                    </div>
                  );
                })}
                <div className="dropdown-footer">More models</div>
              </div>
            )}
          </div>
        </div>
        
        {/* New Chat Button (moved to right side) */}
        <div className="right-controls">
          <button 
            className="header-action-button new-chat" 
            onClick={handleNewChat}
            title="New Chat"
          >
            <span className="new-chat-icon">+</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default Header;
