import React, { useState, useEffect } from 'react';
import WebSocketService from '../services/websocket';
import { useAppState, AgentStatus } from '../context/AppContext';

function MessageInput() {
  const { state, dispatch } = useAppState();
  const { agent, chat } = state;
  const [message, setMessage] = useState('');

  // Add logging for initial render and state changes
  useEffect(() => {
    console.log('MessageInput - Component mounted or updated');
    console.log('Current agent state:', agent);
    console.log('Current chat state:', chat);
  }, [agent, chat]);

  // Add effect to clear input when processing completes
  useEffect(() => {
    if (!agent.processing && !agent.playing) {
      console.log('MessageInput - Clearing input after processing completed');
      setMessage('');
      dispatch({ 
        type: 'SET_CHAT_INPUT', 
        payload: '' 
      });
    }
  }, [agent.processing, agent.playing]);

  const getPlayState = () => {
    const playState = !agent.processing && !agent.playing ? 'stopped' 
                     : agent.processing && agent.playing ? 'running' 
                     : 'stopping';
    console.log('MessageInput - getPlayState:', playState, 'agent:', agent);
    return playState;
  };

  const handleChange = (e) => {
    const newMessage = e.target.value;
    console.log('MessageInput - handleChange:', newMessage);
    setMessage(newMessage);
    dispatch({ 
      type: 'SET_CHAT_INPUT', 
      payload: newMessage 
    });
  };

  const handleSubmit = async (e) => {
    // Add logging at the start of submission
    console.log('MessageInput - Starting submission with message:', message);
    
    e?.preventDefault();
    const playState = getPlayState();
    
    if (!message.trim() || playState !== 'stopped') {
      console.log('MessageInput - handleSubmit cancelled:', { 
        hasMessage: !!message.trim(), 
        playState 
      });
      return;
    }

    try {
      // Add logging before dispatch
      console.log('MessageInput - Dispatching user message');
      
      dispatch({
        type: 'ADD_CHAT_MESSAGE',
        payload: {
          type: 'user',
          text: message.trim(),
          timestamp: new Date().toISOString()
        }
      });

      // Add logging after dispatch
      console.log('MessageInput - Message dispatched, sending to WebSocket');
      
      WebSocketService.sendMessage(message);
      setMessage('');
      dispatch({ 
        type: 'SET_CHAT_INPUT', 
        payload: '' 
      });
    } catch (error) {
      console.error('MessageInput - error sending message:', error);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      console.log('MessageInput - Enter key pressed');
      e.preventDefault();
      handleSubmit();
    }
  };

  const playState = getPlayState();
  console.log('MessageInput - Render:', { 
    playState, 
    message, 
    isDisabled: playState !== 'stopped' 
  });

  const isInputEnabled = agent.status === AgentStatus.IDLE;

  return (
    <div className="message-input-container">
      <input 
        type="text" 
        className="message-input" 
        placeholder={
          agent.status === AgentStatus.IDLE 
            ? "Ask Compass ..." 
            : "Processing..."
        }
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={!isInputEnabled}
      />
    </div>
  );
}

export default MessageInput; 