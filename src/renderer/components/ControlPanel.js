import React from 'react';
import WebSocketService from '../services/websocket';
import { useAppState } from '../context/AppContext';

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;

  const handlePlayToggle = () => {
    if (!agentState.processing && !agentState.playing) {
      if (chat.currentInput?.trim()) {
        dispatch({ type: 'START_PROCESSING' });
        WebSocketService.sendMessage(chat.currentInput);
      }
    } else {
      dispatch({ type: 'STOP_PROCESSING' });
      WebSocketService.updateControlState({ playing: false });
    }
  };

  const handleAutoModeToggle = () => {
    const newAutoMode = !agentState.autoMode;
    WebSocketService.updateControlState({ 
      autoMode: newAutoMode,
      highlightMode: newAutoMode ? false : agentState.highlightMode 
    });
  };

  const handleHighlightToggle = () => {
    if (!agentState.autoMode) {
      WebSocketService.updateControlState({ 
        highlightMode: !agentState.highlightMode 
      });
    }
  };

  const getPlayButtonIcon = () => {
    if (agentState.processing && agentState.playing) return '⏸️';
    if (agentState.processing && !agentState.playing) return '⏳';
    return '▶️';
  };

  return (
    <div className="control-panel">
      <button 
        className={`control-button ${agentState.autoMode ? 'active' : ''}`}
        onClick={handleAutoModeToggle}
        title={agentState.autoMode ? "Automatic Mode (On)" : "Automatic Mode (Off)"}
      >
        <i className="icon-auto">
          {agentState.autoMode ? '➡️➡️➡️' : '➡️'}
        </i>
      </button>
      
      <button 
        className={`control-button ${agentState.highlightMode ? 'active' : ''}`}
        onClick={handleHighlightToggle}
        disabled={agentState.autoMode}
        title={agentState.highlightMode ? "Highlight Mode (On)" : "Highlight Mode (Off)"}
      >
        <i className="icon-highlight">
          {agentState.highlightMode ? '💡' : 'ℹ️'}
        </i>
      </button>
      
      <button 
        className={`control-button ${agentState.playing ? 'active' : ''}`}
        onClick={handlePlayToggle}
        disabled={!chat.currentInput?.trim() && !agentState.processing}
        title={agentState.playing ? "Stop" : "Start"}
      >
        <i className="icon-play">{getPlayButtonIcon()}</i>
      </button>
    </div>
  );
}

export default ControlPanel; 