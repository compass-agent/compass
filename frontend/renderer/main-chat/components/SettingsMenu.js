import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faArrowUpRightFromSquare,
  faEye,
  faEyeSlash,
  faCog,
} from "@fortawesome/free-solid-svg-icons";
import "../styles/Header.scss";

function SettingsMenu({ onClose }) {
  const [agentName, setAgentName] = React.useState("structural-engineer"); // TODO: update it to Generic later
  const [showAgentOptions, setShowAgentOptions] = React.useState(false);
  const [viewScreen, setViewScreen] = React.useState(false);
  const [modelName, setModelName] = React.useState("Claude Sonnet 3.5");
  const [showModelOptions, setShowModelOptions] = React.useState(false);
  let isMac = window.electron.platform === "darwin";
  const agentOptions = ["Generic", "FreeCAD", "OpenFoam", "structural-engineer"];
  const modelOptions = [
    "Claude Sonnet 3.5",
    "OpenAI GPT-4O",
    "Google Gemini 2.0",
    "DeepSeek R1",
  ];

  const handleTrainAgent = () => {
    window.electron.ipcRenderer.send("open-template-training");
  };

  const handleAgentSettings = (e, agent) => {
    e.stopPropagation(); // Prevent the agent selection when clicking the settings icon
    console.log(`Settings clicked for ${agent}`); // Placeholder for future implementation
  };

  return (
    <div
      className={`settings-menu ${isMac ? "mac" : "win"}`}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Agent Selection */}
      <div className="menu-section">
        <div
          className="model-selector"
          onClick={() => setShowAgentOptions(!showAgentOptions)}
        >
          <span>Agent: {agentName}</span>
        </div>
        {showAgentOptions && (
          <div className="model-options">
            {agentOptions.map((agent) => (
              <button
                key={agent}
                onClick={() => {
                  setAgentName(agent);
                  setShowAgentOptions(false);
                }}
                className={`agent-option ${
                  agentName === agent ? "selected" : ""
                }`}
              >
                <span>{agent}</span>
                <FontAwesomeIcon
                  icon={faCog}
                  className="settings-icon"
                  onClick={(e) => handleAgentSettings(e, agent)}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Model Selection */}
      <div className="menu-section">
        <div
          className="model-selector"
          onClick={() => setShowModelOptions(!showModelOptions)}
        >
          <span>Model: {modelName}</span>
        </div>
        {showModelOptions && (
          <div className="model-options">
            {modelOptions.map((model) => (
              <button
                key={model}
                onClick={() => {
                  setModelName(model);
                  setShowModelOptions(false);
                }}
                className={modelName === model ? "selected" : ""}
              >
                {model}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* View Screen Toggle */}
      <div className="menu-section">
        <button
          className="toggle-button"
          onClick={() => setViewScreen(!viewScreen)}
        >
          <FontAwesomeIcon
            icon={viewScreen ? faEye : faEyeSlash}
            className={viewScreen ? "enabled" : ""}
          />
          <span>View Screen</span>
        </button>
      </div>

      <div className="menu-divider"></div>

      {/* Action Buttons */}
      <div className="menu-section">
        <button className="action-button" onClick={handleTrainAgent}>
          <span>Train Agent</span>
          <FontAwesomeIcon
            icon={faArrowUpRightFromSquare}
            className="arrow-icon"
          />
        </button>

        <button className="action-button">
          <span>Create Workflow</span>
          <FontAwesomeIcon
            icon={faArrowUpRightFromSquare}
            className="arrow-icon"
          />
        </button>
      </div>

      <div className="menu-divider"></div>

      {/* Settings Placeholder */}
      <div className="menu-section">
        <button className="action-button">
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
}

export default SettingsMenu;
