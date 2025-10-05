import React, { useState } from "react"
import { ActionTypes, AgentMode, AgentStatus } from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import WebSocketService from "../../common/services/websocket"
import "../styles/ControlPanel.scss"

// Custom SVG Icons
const PlayIcon = () => (
  <svg
    width="36"
    height="36"
    viewBox="0 0 120 120"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="60"
      cy="60"
      r="55"
      stroke="#9E61CA"
      strokeOpacity="0.48"
      strokeWidth="10"
    />
    <path
      d="M81.2887 57.2938C84.5436 59.2326 84.5436 63.9462 81.2887 65.885L48.8088 85.2326C45.476 87.2179 41.25 84.8163 41.25 80.937V42.2418C41.25 38.3625 45.476 35.9609 48.8088 37.9462L81.2887 57.2938Z"
      fill="#9E61CA"
    />
  </svg>
)

const StopIcon = () => (
  <svg
    width="36"
    height="36"
    viewBox="0 0 120 120"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="60"
      cy="60"
      r="55"
      stroke="#9E61CA"
      strokeOpacity="0.48"
      strokeWidth="10"
    />
    <rect x="36" y="36" width="48" height="48" rx="5" fill="#9E61CA" />
  </svg>
)

const FastForwardIcon = () => (
  <svg
    width="36"
    height="36"
    viewBox="0 0 121 121"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="60.6387"
      cy="60.9106"
      r="55"
      stroke="#9E61CA"
      strokeOpacity="0.48"
      strokeWidth="10"
    />
    <path
      d="M98.7887 58.2044C102.044 60.1432 102.044 64.8568 98.7887 66.7956L66.3088 86.1432C62.976 88.1285 58.75 85.7269 58.75 81.8476V43.1524C58.75 39.2731 62.976 36.8715 66.3088 38.8568L98.7887 58.2044Z"
      fill="#9E61CA"
    />
    <rect
      x="31"
      y="36"
      width="20"
      height="52"
      rx="5"
      fill="#9E61CA"
      fillOpacity="0.48"
    />
  </svg>
)

const MODES = {
  MANUAL: { mode: AgentMode.MANUAL, title: "Manual Mode", label: "Trainer" },
  SEMI_AUTO: {
    mode: AgentMode.SEMI_AUTO,
    title: "Semi-Automatic Mode",
    label: "Agent",
  },
  AUTO: { mode: AgentMode.AUTO, title: "Automatic Mode", label: "Auto" },
}

function ControlPanel() {
  const { state, dispatch } = useAppState()
  const { agent: agentState, chat } = state
  const [mode, setMode] = useState(MODES.MANUAL.mode)
  const isAutoMode = agentState.mode === AgentMode.AUTO

  const handleToolsAndNextActionClick = () => {
    WebSocketService.executeToolAndGenerateAction()
  }

  const handlePlayClick = () => {
    console.log("ControlPanel -handlePlayClick: agentState", agentState)
    dispatch({
      type: ActionTypes.ADD_CHAT_MESSAGE,
      payload: {
        type: "user",
        text: chat.currentInput.trim(),
        timestamp: new Date().toISOString(),
      },
    })
    WebSocketService.sendMessage(chat.currentInput)
    dispatch({ type: ActionTypes.SET_CHAT_INPUT, payload: "" })
  }

  const handleStop = () => {
    console.log("ControlPanel handleStop")
    dispatch({
      type: "STOP_PROCESSING",
      payload: "",
    })
    WebSocketService.updateControlState({
      status: AgentStatus.STOPPING,
    })
  }

  const isAgentStatePlaying = agentState.status !== AgentStatus.STOPPED

  const getButtonConfig = () => {
    console.log("ControlPanel: getButtonConfig: - Agent state: ", agentState)
    if (isAgentStatePlaying) {
      return {
        iconComponent: StopIcon,
        loading: true,
        title: "Processing...",
        action: handleStop,
      }
    } else if (agentState.pendingTools > 0 && !chat.currentInput?.trim()) {
      return {
        iconComponent: FastForwardIcon,
        title: "Execute Pending Tools & Generate Next Action",
        action: handleToolsAndNextActionClick,
      }
    } else if (agentState.pendingTools > 0 && chat.currentInput?.trim()) {
      return {
        iconComponent: PlayIcon,
        title: "Process Message & Update Tools",
        action: handlePlayClick,
      } // LLM Response: new tools
    } else if (agentState.pendingTools === 0 && chat.currentInput?.trim()) {
      return {
        iconComponent: PlayIcon,
        title: "Process Message",
        action: handlePlayClick,
      } // message
    } else {
      console.log("ControlPanel: getButtonConfig else: PT0 & Msg0")
      return {
        iconComponent: PlayIcon,
        title: "",
        action: handlePlayClick,
        disable: true,
      } // Default case
    }
  }

  const playButtonConfig = getButtonConfig()

  const setAgentMode = (mode) => {
    WebSocketService.updateControlState({
      mode: mode,
    })
    // Optimistically update the front-end state
    dispatch({
      type: ActionTypes.SET_AGENT_STATE,
      payload: { mode: mode },
    })
  }

  return (
    <div className="control-panel">
      <div className="left-controls">
        <div className="mode-toggle">
          {Object.entries(MODES).map(([key, value]) => (
            <button
              key={key}
              className={`mode-toggle-btn${
                mode === value.mode ? " active" : ""
              }`}
              onClick={() => {
                setMode(value.mode)
                setAgentMode(value.mode)
              }}
              title={value.title}
            >
              {value.label}
            </button>
          ))}
        </div>
      </div>
      <div className="right-controls">
        <button
          className={`button ${isAgentStatePlaying ? "active" : ""}`}
          onClick={playButtonConfig.action}
          title={playButtonConfig.title}
        >
          <playButtonConfig.iconComponent />
        </button>
      </div>
    </div>
  )
}

export default ControlPanel
