import React, { useEffect, useState } from 'react';
import WebSocketService from '../services/websocket';
import { useAppState, AgentStatus } from '../context/AppContext';
import '../styles/ControlPanel.css';

function ControlPanel() {
  const { state, dispatch } = useAppState();
  const { agent: agentState, chat } = state;
  const [lastClickTime, setLastClickTime] = useState(0);

  useEffect(() => {
    console.log('ControlPanel - Agent state updated:', {
      status: agentState.status,
      playing: agentState.playing,
      currentInput: chat.currentInput
    });
  }, [agentState.status, agentState.playing, chat.currentInput]);

  const handlePlayClick = () => {
    const currentTime = new Date().getTime();
    const timeDiff = currentTime - lastClickTime;
    
    if (timeDiff < 300) { // Double click detected
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
        type: 'ADD_CHAT_MESSAGE',
        payload: {
          type: 'user',
          text: chat.currentInput.trim(),
          timestamp: new Date().toISOString()
        }
      });
      WebSocketService.sendMessage(chat.currentInput);
      dispatch({ type: 'SET_CHAT_INPUT', payload: '' });
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
      autoMode: !agentState.autoMode
    });
  };

  const handleHighlightToggle = () => {
    WebSocketService.updateControlState({
      highlightMode: !agentState.highlightMode
    });
  };

  const getPlayButtonIcon = () => {
    if (agentState.status !== AgentStatus.IDLE) {
      return '⏳'; // Processing
    } else if (agentState.pendingTools > 0) {
      return '🔨'; // Pending tools
    } else {
      return '▶️'; // Ready to generate next action
    }
  };

  const getAutoModeIcon = () => {
    return agentState.autoMode ? '⚡️⚡️' : '⚡️';
  };

  const getPlayButtonTitle = () => {
    if (agentState.status !== AgentStatus.IDLE) {
      return 'Processing...';
    } else if (agentState.pendingTools > 0) {
      return 'Execute Next Tool';
    } else if (chat.currentInput?.trim()) {
      return 'Process Message';
    } else {
      return 'Generate Next Action';
    }
  };

  return (
    <div className="control-panel">
      <div className="left-controls">
        <button 
          className={`control-button ${agentState.autoMode ? 'active' : ''}`}
          onClick={handleAutoModeToggle}
          title={agentState.autoMode ? "Automatic Mode (On)" : "Manual Mode (On)"}
        >
          <i className="icon-auto">{getAutoModeIcon()}</i>
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
      </div>
      
      <button 
        className={`control-button ${agentState.playing ? 'active' : ''}`}
        onClick={handlePlayClick}
        disabled={agentState.status !== AgentStatus.IDLE}
        title={getPlayButtonTitle()}
      >
        <i className="icon-play">{getPlayButtonIcon()}</i>
      </button>
    </div>
  );
}

export default ControlPanel; 