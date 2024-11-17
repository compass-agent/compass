import React, { useState } from 'react';

function MessageInput({ onSendMessage }) {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!message.trim() || isLoading) return;

    setIsLoading(true);
    await onSendMessage(message);
    setMessage('');
    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="message-input-container">
      <input 
        type="text" 
        className="message-input" 
        placeholder="Ask Compass ..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={isLoading}
      />
      <button 
        className="send-button"
        onClick={handleSubmit}
        disabled={isLoading}
      >
        <span className="arrow">→</span>
      </button>
    </div>
  );
}

export default MessageInput; 