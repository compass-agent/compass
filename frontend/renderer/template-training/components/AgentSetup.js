import { faInfoCircle } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useState } from "react"
import "../styles/components/AgentSetup.scss"

// Tooltip component similar to SAP configuration
const Tooltip = ({ text, children }) => {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className="tooltip-container">
      <div
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {children}
      </div>
      {showTooltip && <div className="tooltip-content">{text}</div>}
    </div>
  )
}

const AgentSetup = ({ onNext, onTrainUI, existingAgent }) => {
  const [agentName, setAgentName] = useState("")
  const [description, setDescription] = useState("")
  const [prompt, setPrompt] = useState("")
  const [tools, setTools] = useState({
    desktopControl: false,
    commandLine: false,
    fileEditor: false,
  })
  const [configuration, setConfiguration] = useState({
    sapSetup: false,
  })

  useEffect(() => {
    if (existingAgent && existingAgent.name) {
      // Populate all fields with existing agent data
      setAgentName(existingAgent.name || "")
      setDescription(existingAgent.description || "")
      setPrompt(existingAgent.prompt || "")
      setTools({
        desktopControl: existingAgent.tools?.desktopControl || false,
        commandLine: existingAgent.tools?.commandLine || false,
        fileEditor: existingAgent.tools?.fileEditor || false,
      })
      setConfiguration({
        sapSetup: existingAgent.configuration?.sapSetup || false,
      })
    } else {
      // Reset form for new agent
      setAgentName("")
      setDescription("")
      setPrompt("")
      setTools({
        desktopControl: false,
        commandLine: false,
        fileEditor: false,
      })
      setConfiguration({
        sapSetup: false,
      })
    }
  }, [existingAgent])

  const handleToolChange = (toolName) => {
    setTools((prev) => ({
      ...prev,
      [toolName]: !prev[toolName],
    }))
  }

  const handleConfigurationChange = (configName) => {
    setConfiguration((prev) => ({
      ...prev,
      [configName]: !prev[configName],
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (agentName.trim()) {
      const agentData = {
        name: agentName,
        description,
        prompt,
        tools,
        configuration,
      }
      onNext(agentData)
    }
  }

  return (
    <div className="agent-setup">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="agentName">Name</label>
          <input
            id="agentName"
            type="text"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            placeholder="Enter agent name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter a short description of what this agent does"
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>App Training</label>
          <div className="app-training-buttons">
            <button
              type="button"
              className="secondary"
              onClick={() => {
                // TODO: Implement documentation functionality
                console.log(
                  "Documentation button clicked - feature coming soon"
                )
              }}
            >
              Documents
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => {
                const agentData = {
                  name: agentName,
                  description,
                  prompt,
                  tools,
                  configuration,
                }
                if (onTrainUI) {
                  onTrainUI(agentData)
                }
              }}
            >
              Train UI Components
            </button>
          </div>
        </div>

        <div className="form-group">
          <label>Tools</label>
          <div className="tools-section">
            <div className="tool-item">
              <input
                type="checkbox"
                id="desktopControl"
                checked={tools.desktopControl}
                onChange={() => handleToolChange("desktopControl")}
              />
              <label htmlFor="desktopControl">Desktop Control</label>
              <Tooltip text="Control your screen, mouse and keyboard">
                <FontAwesomeIcon icon={faInfoCircle} className="tooltip-icon" />
              </Tooltip>
            </div>
            <div className="tool-item">
              <input
                type="checkbox"
                id="commandLine"
                checked={tools.commandLine}
                onChange={() => handleToolChange("commandLine")}
              />
              <label htmlFor="commandLine">Command Line</label>
              <Tooltip text="Execute command line operations">
                <FontAwesomeIcon icon={faInfoCircle} className="tooltip-icon" />
              </Tooltip>
            </div>
            <div className="tool-item">
              <input
                type="checkbox"
                id="fileEditor"
                checked={tools.fileEditor}
                onChange={() => handleToolChange("fileEditor")}
              />
              <label htmlFor="fileEditor">File Editor</label>
              <Tooltip text="Access and edit project files">
                <FontAwesomeIcon icon={faInfoCircle} className="tooltip-icon" />
              </Tooltip>
            </div>
          </div>
        </div>

        <div className="form-group">
          <label>Configuration</label>
          <div className="tools-section">
            <div className="tool-item">
              <input
                type="checkbox"
                id="sapSetup"
                checked={configuration.sapSetup}
                onChange={() => handleConfigurationChange("sapSetup")}
              />
              <label htmlFor="sapSetup">SAP Setup</label>
              <Tooltip text="Enable SAP configuration setup in the main window">
                <FontAwesomeIcon icon={faInfoCircle} className="tooltip-icon" />
              </Tooltip>
            </div>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="prompt">Prompt</label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a high-level prompt that describes the agent's behavior and capabilities"
            rows={4}
          />
        </div>

        <div className="button-group">
          <button type="submit" className="primary">
            {existingAgent ? "Save Changes" : "Create Agent"}
          </button>
        </div>
      </form>
    </div>
  )
}

export default AgentSetup
