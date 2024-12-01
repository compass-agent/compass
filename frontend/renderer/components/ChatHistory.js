import React from 'react';
import { useAppState } from '../context/AppContext';

function ChatHistory() {
  const { state } = useAppState();
  const { messages } = state.chat;
  
  console.log('ChatHistory - Current messages:', messages);

  const renderMessage = (msg) => {
    console.log('Rendering message:', msg);
    
    switch (msg.type) {
      case 'user':
        return (
          <div className="user-message">
            <span className="message-icon">👤</span>
            <div className="message-content">
              {msg.text}
            </div>
          </div>
        );

      case 'ai_response':
        return (
          <div className="ai-response">
            <span className="message-icon">🤖</span>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        );
      
      case 'tool_use':
        return (
          <div className="tool-use">
            <span className="message-icon">🔧</span>
            <div className="message-content">
              <div className="tool-params">
                {JSON.stringify(msg.parameters, null, 2)}
              </div>
            </div>
          </div>
        );
      
      case 'tool_result':
        return (
          <div className="tool-result">
            <span className="message-icon">📊</span>
            <div className="message-content">
              {msg.error ? (
                <div className="tool-error">{msg.error}</div>
              ) : (
                <>
                  {msg.output && <div className="tool-output">{msg.output}</div>}
                  {msg.has_image && <div className="tool-image-placeholder">[Image]</div>}
                </>
              )}
            </div>
          </div>
        );
      
      default:
        return (
          <div className="message-content">
            {msg.text}
          </div>
        );
    }
  };

  return (
    <div className="chat-history">
      {messages.map((msg, index) => (
        <div 
          key={index} 
          className={`message ${msg.type}`}
        >
          {renderMessage(msg)}
        </div>
      ))}
    </div>
  );
}

export default ChatHistory; 