import React, { useEffect, useState } from "react";
import WebSocketService from "../services/websocket";
import { useAppState } from "../context/AppContext";
import "../styles/ControlPanel.scss";
import { AgentStatus, ActionTypes } from "../constants";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRotateRight,
  faWrench,
  faPlay,
  faForward,
  faLightbulb,
  faInfo,
  faGear,
  faStop,
  faMagicWandSparkles,
} from "@fortawesome/free-solid-svg-icons";

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;
  const [lastClickTime, setLastClickTime] = useState(0);
  const [isWindowMoved, setIsWindowMoved] = useState(false);

  useEffect(() => {
    console.log("ControlPanel - Agent state updated:", {
      status: agentState.status,
      currentInput: chat.currentInput,
    });
    hanldeFullscrenToggle(agentState.autoMode);
  }, [agentState.status, chat.currentInput]);

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
    console.log("ControlPanel -handleSingleClick: agentState", agentState);
    if (agentState.status !== AgentStatus.STOPPED) {
      handleStop();
    } else if (agentState.pendingTools > 0) {
      // Execute next pending tool
      WebSocketService.executeNextTool();
    } else if (chat.currentInput?.trim()) {
      // Process new message
      dispatch({
        type: ActionTypes.ADD_CHAT_MESSAGE,
        payload: {
          type: "user",
          text: chat.currentInput.trim(),
          timestamp: new Date().toISOString(),
        },
      });
      WebSocketService.sendMessage(chat.currentInput);
      dispatch({ type: ActionTypes.SET_CHAT_INPUT, payload: "" });
    } else {
      // Generate next action
      WebSocketService.generateNextAction();
    }
  };

  const handleDoubleClick = () => {
    if (agentState.status !== AgentStatus.STOPPED) {
      handleStop();
    } else {
      WebSocketService.executeNextTool();
      WebSocketService.generateNextAction();
    }
  };

  const handleStop = () => {
    console.log("ControlPanel handleStop");
    if (agentState.status === AgentStatus.STOPPED) return;
    dispatch({
      type: "STOP_PROCESSING",
      payload: "",
    });
    // WebSocketService.updateControlState({
    //   status: AgentStatus.STOPPED,
    // });
    WebSocketService.sendStopProcessing();
  };

  const handleAutoModeToggle = () => {
    console.log(
      "ControlPanel: handleAutoModeToggle: - Agent state: ",
      agentState
    );
    const newAutoMode = !agentState.autoMode;
    WebSocketService.updateControlState({
      autoMode: newAutoMode,
    });
    // Optimistically update the front-end state
    dispatch({
      type: ActionTypes.SET_AGENT_STATE,
      payload: { autoMode: newAutoMode },
    });

    hanldeFullscrenToggle(newAutoMode);
  };

  const hanldeFullscrenToggle = (autoMode) => {
    setIsWindowMoved(false);
    const handleMoveToBottomRightDone = () => {
      console.log("Window moved to bottom-right corner");
      setIsWindowMoved(true);
      // Remove the event listener after handling the event
      window.electron.ipcRenderer.removeListener(
        "move-to-bottom-right-done",
        handleMoveToBottomRightDone
      );
    };

    if (autoMode && agentState.status !== AgentStatus.STOPPED) {
      // Exit fullscreen when switching to auto mode
      window.electron.ipcRenderer.send("toggle-fullscreen", false);

      // Move window to bottom right corner
      window.electron.ipcRenderer.send("move-to-bottom-right");
      // Add the event listener
      window.electron.ipcRenderer.on(
        "move-to-bottom-right-done",
        handleMoveToBottomRightDone
      );
    } else if (agentState.status !== AgentStatus.STOPPED) {
      // Enter fullscreen when switching to manual mode
      window.electron.ipcRenderer.send("toggle-fullscreen", true);
    }

    if (
      autoMode &&
      isWindowMoved &&
      agentState.status === AgentStatus.STOPPED &&
      agentState.pendingTools === 0
    ) {
      // Auto mode tasks have been done
      console.log("ControlPanel: AutoMode Done, then restore window");
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
    if (agentState.status !== AgentStatus.STOPPED) {
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
    console.log("ControlPanel: getPlayButtonIcon: - Agent state: ", agentState);
    if (agentState.status !== AgentStatus.STOPPED) {
      return { icon: faStop, loading: true }; // Processing // faRotateRight shouldSpin: true
    } else if (agentState.pendingTools > 0) {
      return { icon: faWrench }; // Pending tools
    } else {
      return { icon: faPlay }; // Ready to generate next action
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
          className={`button ${agentState.highlightMode ? "active" : ""}`}
          onClick={handleHighlightToggle}
          disabled={agentState.autoMode}
          title={
            agentState.highlightMode
              ? "Highlight Mode (On)"
              : "Highlight Mode (Off)"
          }
        >
          <FontAwesomeIcon
            icon={agentState.highlightMode ? faLightbulb : faInfo}
          />
        </button>
      </div>

      <div className="right-controls">
        <button
          className={`button ${agentState.status !== AgentStatus.STOPPED ? "active" : ""}`}
          onClick={handlePlayClick}
          // disabled={agentState.status !== AgentStatus.STOPPED}
          title={getPlayButtonTitle()}
        >
          <FontAwesomeIcon icon={playButtonIcon.icon} />
          {playButtonIcon.loading && <div className="spinner"></div>}
        </button>
      </div>
    </div>
  );
}

export default ControlPanel;
