import {
  faForwardStep,
  faPlay,
  faStop,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useState } from "react"
import { ActionTypes, AgentMode, AgentStatus } from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import WebSocketService from "../../common/services/websocket"
import "../styles/ControlPanel.scss"

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

  // const getModeIcon = () => {
  //   if (mode === MODES.MANUAL.mode) {
  //     return faUser
  //   } else if (mode === MODES.SEMI_AUTO.mode) {
  //     return faBolt
  //   } else if (mode === MODES.AUTO.mode) {
  //     return faMagicWandSparkles
  //   }
  // }

  const isAgentStatePlaying = agentState.status !== AgentStatus.STOPPED

  const getButtonConfig = () => {
    console.log("ControlPanel: getButtonConfig: - Agent state: ", agentState)
    if (isAgentStatePlaying) {
      return {
        icon: faStop,
        // SVG version (commented out):
        // iconType: "svg",
        // iconSrc: "../../../resources/pause.svg",
        loading: true,
        title: "Processing...",
        action: handleStop,
      }
    } else if (agentState.pendingTools > 0 && !chat.currentInput?.trim()) {
      return {
        icon: faForwardStep,
        // SVG version (commented out):
        // iconType: "fontawesome",
        // icon: faForwardStep,
        title: "Execute Pending Tools & Generate Next Action",
        action: handleToolsAndNextActionClick,
      }
    } else if (agentState.pendingTools > 0 && chat.currentInput?.trim()) {
      return {
        icon: faPlay,
        // SVG version (commented out):
        // iconType: "svg",
        // iconSrc: "../../../resources/play.svg",
        title: "Process Message & Update Tools",
        action: handlePlayClick,
      } // LLM Response: new tools
    } else if (agentState.pendingTools === 0 && chat.currentInput?.trim()) {
      return {
        icon: faPlay,
        // SVG version (commented out):
        // iconType: "svg",
        // iconSrc: "../../../resources/play.svg",
        title: "Process Message",
        action: handlePlayClick,
      } // message
    } else {
      console.log("ControlPanel: getButtonConfig else: PT0 & Msg0")
      return {
        icon: faPlay,
        // SVG version (commented out):
        // iconType: "svg",
        // iconSrc: "../../../resources/play.svg",
        title: "",
        action: handlePlayClick,
        disable: true,
      } // Default case
    }
  }

  const playButtonConfig = getButtonConfig()

  // const handleMode = () => {
  //   console.log(
  //     `ControlPanel: handleMode: current mode ${mode} - Agent state: ${JSON.stringify(
  //       agentState
  //     )}`
  //   )
  //   if (mode === MODES.MANUAL.mode) {
  //     setMode(MODES.SEMI_AUTO.mode)
  //     setAgentMode(AgentMode.SEMI_AUTO)
  //   } else if (mode === MODES.SEMI_AUTO.mode) {
  //     setMode(MODES.AUTO.mode)
  //     setAgentMode(AgentMode.AUTO)
  //   } else if (MODES.AUTO.mode) {
  //     setMode(MODES.MANUAL.mode)
  //     setAgentMode(AgentMode.MANUAL)
  //   }
  //   console.log("ControlPanel: handleMode: - mode: ", mode)
  // }

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
          <FontAwesomeIcon icon={playButtonConfig.icon} />
          {/* SVG version (commented out):
          {playButtonConfig.iconType === "svg" ? (
            <img 
              src={playButtonConfig.iconSrc} 
              alt={playButtonConfig.title}
              style={{
                width: "24px",
                height: "24px"
              }}
            />
          ) : (
            <FontAwesomeIcon icon={playButtonConfig.icon} />
          )}
          */}
        </button>
      </div>
    </div>
  )
}

export default ControlPanel
