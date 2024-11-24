import React, { useEffect } from 'react';
import WebSocketService from '../services/websocket';
import { useAppState } from '../context/AppContext';

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;

  useEffect(() => {
    console.log('ControlPanel - Agent state updated:', {
      processing: agentState.processing,
      playing: agentState.playing,
      currentInput: chat.currentInput
    });
  }, [agentState.processing, agentState.playing, chat.currentInput]);

  const handlePlayToggle = () => {
    console.log('ControlPanel - Play toggle clicked:', {
      processing: agentState.processing,
      playing: agentState.playing
    });

    if (!agentState.processing && !agentState.playing) {
      if (chat.currentInput?.trim()) {
        WebSocketService.sendMessage(chat.currentInput);
      }
    } else {
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