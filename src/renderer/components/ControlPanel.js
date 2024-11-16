import React, { useState, useEffect } from 'react';
import WebSocketService from '../services/websocket';
import StateManager from '../services/stateManager';

// Define play states as constants
const PLAY_STATES = {
  STOPPED: 'stopped',
  RUNNING: 'running',
  STOPPING: 'stopping'
};

// Add at the top of the file
const logState = (message, state = {}) => {
  console.log(`[ControlPanel] ${message}`, {
    timestamp: new Date().toISOString(),
    ...state
  });
};

function ControlPanel() {
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [isHighlightMode, setIsHighlightMode] = useState(false);
  const [playState, setPlayState] = useState(PLAY_STATES.STOPPED);
  const [currentInput, setCurrentInput] = useState('');

  useEffect(() => {
    return StateManager.subscribe('agent', (state) => {
      logState('Received agent state update:', {
        autoMode: state.autoMode,
        highlightMode: state.highlightMode,
        playing: state.playing,
        processing: state.processing,
        currentPlayState: playState,
      });

      setIsAutoMode(state.autoMode);
      setIsHighlightMode(state.highlightMode);
      
      // Log state transition logic
      if (!state.processing && !state.playing) {
        logState('Transitioning to STOPPED state', { reason: 'not processing and not playing' });
        setPlayState(PLAY_STATES.STOPPED);
      } else if (state.processing && state.playing) {
        logState('Transitioning to RUNNING state', { reason: 'processing and playing' });
        setPlayState(PLAY_STATES.RUNNING);
      } else if (state.processing && !state.playing) {
        logState('Transitioning to STOPPING state', { reason: 'processing but not playing' });
        setPlayState(PLAY_STATES.STOPPING);
      } else {
        logState('Unexpected state combination', {
          processing: state.processing,
          playing: state.playing
        });
      }
    });
  }, [playState]); // Added playState to dependencies

  useEffect(() => {
    logState('PlayState changed', { newPlayState: playState });
  }, [playState]);

  useEffect(() => {
    return StateManager.subscribe('chat.currentInput', (input) => {
      logState('Current input updated', { input });
      setCurrentInput(input);
    });
  }, []);

  const handlePlayStateToggle = () => {
    logState('Play button clicked', { 
      currentPlayState: playState,
      hasInput: Boolean(currentInput?.trim())
    });

    switch (playState) {
      case PLAY_STATES.STOPPED:
        if (currentInput?.trim()) {
          logState('Starting new task', { input: currentInput });
          setPlayState(PLAY_STATES.RUNNING);
          WebSocketService.sendMessage(currentInput);
        } else {
          logState('Cannot start - no input');
        }
        break;
      case PLAY_STATES.RUNNING:
        logState('Requesting stop');
        setPlayState(PLAY_STATES.STOPPING);
        WebSocketService.updateControlState({ playing: false });
        break;
      case PLAY_STATES.STOPPING:
        logState('Already stopping - button should be disabled');
        break;
      default:
        logState('Unexpected play state', { playState });
        break;
    }
  };

  const handleAutoModeToggle = () => {
    const newState = !isAutoMode;
    logState('Auto mode toggled', { newState });
    setIsAutoMode(newState);
    WebSocketService.updateControlState({ autoMode: newState });
    if (newState) {
      setIsHighlightMode(false);
    }
  };

  const handleHighlightToggle = () => {
    if (!isAutoMode) {
      const newState = !isHighlightMode;
      logState('Highlight mode toggled', { newState });
      setIsHighlightMode(newState);
      WebSocketService.updateControlState({ highlightMode: newState });
    } else {
      logState('Cannot toggle highlight mode - auto mode is active');
    }
  };

  const getPlayStateIcon = () => {
    switch (playState) {
      case PLAY_STATES.RUNNING:
        return '⏸️'; // Running, can be paused
      case PLAY_STATES.STOPPING:
        return '⏳'; // Stopping in progress
      case PLAY_STATES.STOPPED:
        return '▶️'; // Stopped, can be started
      default:
        return '▶️';
    }
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
        className={`control-button ${playState === PLAY_STATES.RUNNING ? 'active' : ''}`}
        onClick={handlePlayStateToggle}
        disabled={playState === PLAY_STATES.STOPPING}
        title={playState.charAt(0).toUpperCase() + playState.slice(1)}
      >
        <i className="icon-play">
          {getPlayStateIcon()}
        </i>
      </button>
    </div>
  );
}

export default ControlPanel; 