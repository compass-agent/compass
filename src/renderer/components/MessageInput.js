import React, { useState } from 'react';
import WebSocketService from '../services/websocket';
import { useAppState } from '../context/AppContext';

function MessageInput() {
  const { state, dispatch } = useAppState();
  const { agent, chat } = state;
  const [message, setMessage] = useState('');

  const getPlayState = () => {
    if (!agent.processing && !agent.playing) return 'stopped';
    if (agent.processing && agent.playing) return 'running';
    return 'stopping';
  };

  const handleChange = (e) => {
    const newMessage = e.target.value;
    setMessage(newMessage);
    dispatch({ 
      type: 'SET_CHAT_INPUT', 
      payload: newMessage 
    });
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    const playState = getPlayState();
    
    if (!message.trim() || playState !== 'stopped') return;

    try {
      WebSocketService.sendMessage(message);
      setMessage('');
      dispatch({ 
        type: 'SET_CHAT_INPUT', 
        payload: '' 
      });
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.message 
      });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const playState = getPlayState();

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