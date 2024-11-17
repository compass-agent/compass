import React from 'react';

function ChatHistory({ messages }) {
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