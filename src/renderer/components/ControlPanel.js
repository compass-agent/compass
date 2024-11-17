import React, { useState } from 'react';

function ControlPanel() {
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [isHighlightMode, setIsHighlightMode] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleAutoModeToggle = () => {
    setIsAutoMode(!isAutoMode);
    if (!isAutoMode) {
      setIsHighlightMode(false);
    }
  };

  const handleHighlightToggle = () => {
    if (!isAutoMode) {
      setIsHighlightMode(!isHighlightMode);
    }
  };

  const handlePlayPauseToggle = () => {
    setIsPlaying(!isPlaying);
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
          {isPlaying ? '⏸️' : '▶️'}
        </i>
      </button>
    </div>
  );
}

export default ControlPanel; 