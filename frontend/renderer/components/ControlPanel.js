import React, { useEffect, useState } from "react";
import WebSocketService from "../services/websocket";
import { useAppState } from "../context/AppContext";
import "../styles/ControlPanel.scss";
import { AgentStatus, ActionTypes, AgentMode } from "../constants";
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
  faScrewdriverWrench,
  faWandMagic
} from "@fortawesome/free-solid-svg-icons";

const MODES = {
  MANUAL: {mode: AgentMode.MANUAL , title: "Manual Mode"},
  SEMI_AUTO: {mode: AgentMode.SEMI_AUTO, title: "Semi-Automatic Mode"},
  AUTO: {mode: AgentMode.AUTO, title: "Automatic Mode"},
  HIGHLIGHT: {mode: "HighLight", title: "Highlight Mode" }
};

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;
  const [isWindowMoved, setIsWindowMoved] = useState(false);
  const [mode, setMode] = useState(MODES.MANUAL.mode);
  const isAutoMode = agentState.mode === AgentMode.AUTO;

  useEffect(() => {
    console.log("ControlPanel - Agent state updated:", {
      status: agentState.status,
      currentInput: chat.currentInput,
    });
    hanldeFullscrenToggle(isAutoMode);
  }, [agentState.status, chat.currentInput]);

  const handleToolsClick = () => {
    WebSocketService.executeNextTool();
  };

  const handleToolsAndNextActionClick = () => {

    WebSocketService.executeNextTool();
    WebSocketService.generateNextAction();
  };

  const handlePlayClick = () => {
    console.log("ControlPanel -handlePlayClick: agentState", agentState);
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
      //TODO:Process Message & Update Tools: update backend and pending tools based on LLM response
  };

  const handleStop = () => {
    console.log("ControlPanel handleStop");
    dispatch({
      type: "STOP_PROCESSING",
      payload: "",
    });
    WebSocketService.updateControlState({
      status: AgentStatus.STOPPING,
    });
  };


  const hanldeFullscrenToggle = (isAutoMode) => {
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

    if (isAutoMode && agentState.status !== AgentStatus.STOPPED) {
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
      isAutoMode &&
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

  const getModeIcon = () => {
    if (mode === MODES.MANUAL.mode) {
      return faGear;
    } else if (mode === MODES.SEMI_AUTO.mode) {
      return faWandMagic;
    } else if (mode === MODES.AUTO.mode) {
      return faMagicWandSparkles;
    }
  };

  const getToolsButtonTitle = () => {
    console.log("ControlPanel: getToolsButtonTitle: - Agent state: ", agentState);
    if (agentState.status !== AgentStatus.STOPPED) {
      return "Processing...";
    } else if (agentState.pendingTools > 0) {
      return "Execute Next Tool";
    } else {
      return "Generate Next Action";
    }
  };

  const isAgentStatePlaying = agentState.status !== AgentStatus.STOPPED;

  const getButtonConfig = () => {
    console.log("ControlPanel: getButtonConfig: - Agent state: ", agentState);
    if (isAgentStatePlaying) {
      return { icon: faStop, loading: true, title: 'Processing...', action: handleStop };
    } else if (agentState.pendingTools > 0 && !chat.currentInput?.trim()) {
      return { icon: faScrewdriverWrench, title: 'Execute Pending Tools & Generate Next Action', action: handleToolsAndNextActionClick };
    } else if (agentState.pendingTools > 0 && chat.currentInput?.trim()) {
      return { icon: faPlay, title: 'Process Message & Update Tools', action: handlePlayClick }; // LLM Response: new tools
    } else if (agentState.pendingTools === 0 && chat.currentInput?.trim()) {
      return { icon: faPlay, title: 'Process Message', action: handlePlayClick }; // message
    } else {
      console.log("ControlPanel: getButtonConfig else: PT0 & Msg0")
      return { icon: faPlay, title: '', action: handlePlayClick, disable: true }; // Default case
    }
  };

  const playButtonConfig = getButtonConfig();

  const handleMode = () => {
    console.log(
      `ControlPanel: handleMode: current mode ${mode} - Agent state: ${JSON.stringify(agentState)}`);
    if (mode === MODES.MANUAL.mode) {
      setMode(MODES.SEMI_AUTO.mode);
      setAgentMode(AgentMode.SEMI_AUTO);
    } else if (mode === MODES.SEMI_AUTO.mode) {
      setMode(MODES.AUTO.mode);
      setAgentMode(AgentMode.AUTO);
      hanldeFullscrenToggle(true);
    } else if (MODES.AUTO.mode) {
      setMode(MODES.MANUAL.mode)
      setAgentMode(AgentMode.MANUAL);
      hanldeFullscrenToggle(false);
    }
    console.log(
      "ControlPanel: handleMode: - mode: ",
      mode
    );
  };

  const setAgentMode = (mode) => {
    WebSocketService.updateControlState({
      mode: mode,
    });
    // Optimistically update the front-end state
    dispatch({
      type: ActionTypes.SET_AGENT_STATE,
      payload: { mode: mode },
    });
  }  

  return (
    <div className="control-panel">
      <div className="left-controls">
        <button
          className="button active"
          // className={`button ${mode === MODES.AUTO.mode || mode === MODES.SEMI_AUTO.mode ? "active" : ""}`}
          onClick={handleMode}
          title={
            mode === MODES.AUTO.mode ? MODES.AUTO.title : mode === MODES.SEMI_AUTO.mode ? MODES.SEMI_AUTO.title : MODES.MANUAL.title }
        >
          <FontAwesomeIcon icon={getModeIcon()} />
        </button>

       { mode === MODES.MANUAL.mode && ( <button
          className={`button ${agentState.highlightMode ? "active" : ""}`}
          onClick={handleHighlightToggle}
          title={
            agentState.highlightMode
              ? "Highlight Mode (On)"
              : "Highlight Mode (Off)"
          }
        >
          <FontAwesomeIcon
            icon={faLightbulb }
          />
        </button>)}
      </div>

      <div className="right-controls">
        {!isAutoMode && agentState.pendingTools > 0 && (
          <button
            className={`button ${isAgentStatePlaying ? "active" : ""}`}
            onClick={handleToolsClick}
            title={getToolsButtonTitle()}
          >
            <FontAwesomeIcon icon={faWrench} />
          </button>
        )}
        <button
          className={`button ${isAgentStatePlaying ? "active" : ""}`}
          onClick={playButtonConfig.action}
          title={playButtonConfig.title}
        >
          <FontAwesomeIcon icon={playButtonConfig.icon} />
        </button>
      </div>
    </div>
  );
}

export default ControlPanel;
