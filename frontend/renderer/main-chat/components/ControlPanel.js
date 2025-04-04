import React, { useState } from "react";
import WebSocketService from "../../common/services/websocket";
import { useAppState } from "../../common/context/AppContext";
import "../styles/ControlPanel.scss";
import { AgentStatus, ActionTypes, AgentMode } from '../../common/constants';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPlay,
  faStop,
  faMagicWandSparkles,
  faForwardFast,
  faBolt,
  faUser
} from "@fortawesome/free-solid-svg-icons";

const MODES = {
  MANUAL: {mode: AgentMode.MANUAL , title: "Manual Mode"},
  SEMI_AUTO: {mode: AgentMode.SEMI_AUTO, title: "Semi-Automatic Mode"},
  AUTO: {mode: AgentMode.AUTO, title: "Automatic Mode"}
};

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;
  const [mode, setMode] = useState(MODES.MANUAL.mode);
  const isAutoMode = agentState.mode === AgentMode.AUTO;

  const handleToolsAndNextActionClick = () => {
    WebSocketService.executeToolAndGenerateAction();
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

  const getModeIcon = () => {
    if (mode === MODES.MANUAL.mode) {
      return faUser;
    } else if (mode === MODES.SEMI_AUTO.mode) {
      return faBolt;
    } else if (mode === MODES.AUTO.mode) {
      return faMagicWandSparkles;
    }
  };

  const isAgentStatePlaying = agentState.status !== AgentStatus.STOPPED;

  const getButtonConfig = () => {
    console.log("ControlPanel: getButtonConfig: - Agent state: ", agentState);
    if (isAgentStatePlaying) {
      return { icon: faStop, loading: true, title: 'Processing...', action: handleStop };
    } else if (agentState.pendingTools > 0 && !chat.currentInput?.trim()) {
      return { icon:  faForwardFast , title: 'Execute Pending Tools & Generate Next Action', action: handleToolsAndNextActionClick };
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
    } else if (MODES.AUTO.mode) {
      setMode(MODES.MANUAL.mode)
      setAgentMode(AgentMode.MANUAL);
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
          onClick={handleMode}
          title={
            mode === MODES.AUTO.mode ? MODES.AUTO.title : mode === MODES.SEMI_AUTO.mode ? MODES.SEMI_AUTO.title : MODES.MANUAL.title }
        >
          <FontAwesomeIcon icon={getModeIcon()} />
        </button>
      </div>
      <div className="right-controls">
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
