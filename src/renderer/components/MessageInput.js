import React, { useState, useEffect } from 'react';
import StateManager from '../services/stateManager';
import WebSocketService from '../services/websocket';

function MessageInput() {
  const [message, setMessage] = useState('');
  const [playState, setPlayState] = useState('stopped');

  useEffect(() => {
    return StateManager.subscribe('agent', (state) => {
      if (!state.processing && !state.playing) {
        setPlayState('stopped');
      } else if (state.processing && state.playing) {
        setPlayState('running');
      } else if (!state.playing) {
        setPlayState('stopping');
      }
    });
  }, []);

  const handleChange = (e) => {
    const newMessage = e.target.value;
    setMessage(newMessage);
    StateManager.setState('chat.currentInput', newMessage);
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!message.trim() || playState !== 'stopped') return;

    try {
      WebSocketService.sendMessage(message);
      setMessage('');
      StateManager.setState('chat.currentInput', '');
    } catch (error) {
      StateManager.setState('chat.error', error.message);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="message-input-container">
      <input 
        type="text" 
        className="message-input" 
        placeholder={playState !== 'stopped' ? "Processing..." : "Ask Compass ..."}
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={playState !== 'stopped'}
      />
    </div>
  );
}

export default MessageInput; 