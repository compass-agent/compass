import React, { useEffect } from 'react';
import WebSocketService from '../services/websocket';
import { useAppState, AgentStatus } from '../context/AppContext';
import '../styles/ControlPanel.css';

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;

  useEffect(() => {
    console.log('ControlPanel - Agent state updated:', {
      status: agentState.status,
      playing: agentState.playing,
      currentInput: chat.currentInput
    });
  }, [agentState.status, agentState.playing, chat.currentInput]);

  const handlePlayToggle = () => {
    console.log('ControlPanel - Play toggle clicked:', {
      status: agentState.status,
      playing: agentState.playing,
      currentInput: chat.currentInput
    });

    if (agentState.status === AgentStatus.IDLE && !agentState.playing) {
      if (chat.currentInput?.trim()) {
        dispatch({
          type: 'ADD_CHAT_MESSAGE',
          payload: {
            type: 'user',
            text: chat.currentInput.trim(),
            timestamp: new Date().toISOString()
          }
        });

        WebSocketService.sendMessage(chat.currentInput);
        
        dispatch({ 
          type: 'SET_CHAT_INPUT', 
          payload: '' 
        });
      }
    } else if (agentState.status === AgentStatus.RUNNING) {
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
    switch (agentState.status) {
      case AgentStatus.RUNNING:
        return '⏸️';
      case AgentStatus.STOPPING:
        return '⏳';
      default:
        return '▶️';
    }
  };

  const getAutoModeIcon = () => {
    return agentState.autoMode ? '⚡️⚡️' : '⚡️';
  };

  return (
    <div className="control-panel">
      <button 
        className={`control-button ${agentState.autoMode ? 'active' : ''}`}
        onClick={handleAutoModeToggle}
        title={agentState.autoMode ? "Automatic Mode (On)" : "Manual Mode (On)"}
      >
        <i className="icon-auto">
          {getAutoModeIcon()}
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
        disabled={
          !chat.currentInput?.trim() && agentState.status === AgentStatus.IDLE ||
          agentState.status === AgentStatus.STOPPING
        }
        title={agentState.playing ? "Stop" : "Start"}
      >
        <i className="icon-play">{getPlayButtonIcon()}</i>
      </button>
    </div>
  );
}

export default ControlPanel; 