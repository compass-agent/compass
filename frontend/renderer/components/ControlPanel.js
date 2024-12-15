import React, { useEffect, useState } from "react";
import WebSocketService from "../services/websocket";
import { useAppState } from "../context/AppContext";
import "../styles/ControlPanel.scss";
import { AgentStatus } from "../constants";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRotateRight, faWrench, faPlay, faForward, faLightbulb, faInfo, faGear, faMagicWandSparkles  } from "@fortawesome/free-solid-svg-icons";

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;
  const [lastClickTime, setLastClickTime] = useState(0);

  useEffect(() => {
    console.log("ControlPanel - Agent state updated:", {
      status: agentState.status,
      playing: agentState.playing,
      currentInput: chat.currentInput,
    });
  }, [agentState.status, agentState.playing, chat.currentInput]); // playing boolean

  const handlePlayClick = () => {
    const currentTime = new Date().getTime();
    const timeDiff = currentTime - lastClickTime;

    if (timeDiff < 300) {
      // Double click detected
      handleDoubleClick();
    } else {
      handleSingleClick();
      setLastClickTime(currentTime);
    }
  };

  const handleSingleClick = () => {
    if (agentState.status !== AgentStatus.IDLE) return;

    if (agentState.pendingTools > 0) {
      // Execute next pending tool
      WebSocketService.executeNextTool();
    } else if (chat.currentInput?.trim()) {
      // Process new message
      dispatch({
        type: "ADD_CHAT_MESSAGE",
        payload: {
          type: "user",
          text: chat.currentInput.trim(),
          timestamp: new Date().toISOString(),
        },
      });
      WebSocketService.sendMessage(chat.currentInput);
      dispatch({ type: "SET_CHAT_INPUT", payload: "" });
    } else {
      // Generate next action
      WebSocketService.generateNextAction();
    }
  };

  const handleDoubleClick = () => {
    if (agentState.status !== AgentStatus.IDLE) return;
    WebSocketService.executeNextTool();
    WebSocketService.generateNextAction();
  };

  const handleAutoModeToggle = () => {
    WebSocketService.updateControlState({
      autoMode: !agentState.autoMode,
    });
    if (!agentState.autoMode) {
      // Exit fullscreen when switching to auto mode
      window.electron.ipcRenderer.send("toggle-fullscreen", false);
    } else {
      // Enter fullscreen when switching to manual mode
      window.electron.ipcRenderer.send("toggle-fullscreen", true);
    }
  };

  const handleHighlightToggle = () => {
    WebSocketService.updateControlState({
      highlightMode: !agentState.highlightMode,
    });
  };

  const autoManualModeIconToggel = () => {
    return agentState.autoMode ? faMagicWandSparkles : faGear;
  };

  const getPlayButtonTitle = () => {
    if (agentState.status !== AgentStatus.IDLE) {
      return "Processing...";
    } else if (agentState.pendingTools > 0) {
      return "Execute Next Tool";
    } else if (chat.currentInput?.trim()) {
      return "Process Message";
    } else {
      return "Generate Next Action";
    }
  };

  const getPlayButtonIcon = () => {
    console.log("ControlPanel: getPlayButtonIcon: - Agent state: ", agentState)
    if (agentState.status !== AgentStatus.IDLE) {
      return {icon: faRotateRight, shouldSpin: true}; // Processing
    } else if (agentState.pendingTools > 0) {
      return {icon: faWrench }; // Pending tools
    } else {
      return {icon: faPlay};  // Ready to generate next action
    }
  };
  const playButtonIcon = getPlayButtonIcon();
  return (
    <div className="control-panel">
      <div className="left-controls">
        <button
          className={`button ${agentState.autoMode ? "active" : ""}`}
          onClick={handleAutoModeToggle}
          title={
            agentState.autoMode ? "Automatic Mode (On)" : "Manual Mode (On)"
          }
        >
          <FontAwesomeIcon icon={autoManualModeIconToggel()} />
        </button>

        <button
          className={`button ${
            agentState.highlightMode ? "active" : ""
          }`}
          onClick={handleHighlightToggle}
          disabled={agentState.autoMode}
          title={
            agentState.highlightMode
              ? "Highlight Mode (On)"
              : "Highlight Mode (Off)"
          }
        >
          <FontAwesomeIcon icon={agentState.highlightMode ? faLightbulb : faInfo } />
        </button>
      </div>

      <div className="right-controls">
        <button
          className={`button ${agentState.playing ? "active" : ""}`}
          onClick={handlePlayClick}
          disabled={agentState.status !== AgentStatus.IDLE}
          title={getPlayButtonTitle()}
        >
          <FontAwesomeIcon icon={playButtonIcon.icon} spin={playButtonIcon.spin} />
        </button>
      </div>
    </div>
  );
}

export default ControlPanel;
