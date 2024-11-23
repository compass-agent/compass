import React from 'react';
import { useAppState } from '../context/AppContext';

function ChatHistory() {
  const { state } = useAppState();
  const { messages } = state.chat;

  return (
    <div className="chat-history">
      {messages.map((msg, index) => (
        <div 
          key={index} 
          className={`message ${msg.type}`}
        >
          <div className="message-content">
            {msg.text}
          </div>
        </div>
      ))}
    </div>
  );
}

export default ChatHistory; 