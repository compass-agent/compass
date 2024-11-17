import React, { useState, useEffect } from 'react';
import WebSocketService from '../services/websocket';

function ControlPanel() {
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [isHighlightMode, setIsHighlightMode] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    WebSocketService.onMessage('state_update', (state) => {
      setIsAutoMode(state.is_auto_mode);
      setIsHighlightMode(state.is_highlight_mode);
      setIsPlaying(state.is_playing);
      setIsProcessing(state.is_processing);
    });
  }, []);

  const handleAutoModeToggle = () => {
    const newState = !isAutoMode;
    setIsAutoMode(newState);
    WebSocketService.updateControlState({ auto_mode: newState });
    if (newState) {
      setIsHighlightMode(false);
    }
  };

  const handleHighlightToggle = () => {
    if (!isAutoMode) {
      const newState = !isHighlightMode;
      setIsHighlightMode(newState);
      WebSocketService.updateControlState({ highlight_mode: newState });
    }
  };

  const handlePlayPauseToggle = () => {
    const newState = !isPlaying;
    setIsPlaying(newState);
    WebSocketService.updateControlState({ playing: newState });
  };

  return (
    <div className="control-panel">
      <button 
        className={`control-button ${isAutoMode ? 'active' : ''}`}
        onClick={handleAutoModeToggle}
        title={isAutoMode ? "Automatic Mode (On)" : "Automatic Mode (Off)"}
      >
        <i className="icon-auto">
          {isAutoMode ? '➡️➡️➡️' : '➡️'}
        </i>
      </button>
      <button 
        className={`control-button ${isHighlightMode ? 'active' : ''}`}
        onClick={handleHighlightToggle}
        disabled={isAutoMode}
        title={isHighlightMode ? "Highlight Mode (On)" : "Highlight Mode (Off)"}
      >
        <i className="icon-highlight">
          {isHighlightMode ? '💡' : 'ℹ️'}
        </i>
      </button>
      <button 
        className={`control-button ${isPlaying ? 'active' : ''}`}
        onClick={handlePlayPauseToggle}
        title={isPlaying ? "Pause" : "Play"}
      >
        <i className="icon-play">
          {isPlaying ? '▶️' : '⏸️'}
        </i>
      </button>
    </div>
  );
}

export default ControlPanel; 