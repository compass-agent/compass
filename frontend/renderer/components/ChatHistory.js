import React, { useRef, useState, useEffect } from 'react';
import { useAppState } from '../context/AppContext';
import '../styles/ChatHistory.scss';

const TOOL_ACTION_MAPPING = {
  screenshot: { icon: '📸', text: 'Taking screenshot...' },
  click: { icon: '🖱️', text: 'Clicking element' },
  type: { icon: '⌨️', text: 'Typing text' },
  // Add more mappings as needed
};

function ChatHistory() {
  const { state } = useAppState();
  const { messages } = state.chat;
  const chatRef = useRef(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  console.log('ChatHistory - Current messages:', messages);

  // Add scroll to bottom effect
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [state.chat.messages]);

  // Add the missing getRecentMessages function
  const getRecentMessages = () => {
    if (!messages.length) return [];
    
    // Find the index of the most recent AI response
    const lastAiIndex = [...messages].reverse().findIndex(msg => msg.type === 'ai_response');
    
    if (lastAiIndex === -1) {
      // If no AI response found, return just the last message
      return messages.slice(-1);
    }
    
    // Return the AI response and all subsequent messages
    return messages.slice(-(lastAiIndex + 1));
  };

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
        const action = msg.parameters?.action;
        const mapping = TOOL_ACTION_MAPPING[action] || { icon: '🔧', text: 'Performing action' };
        return (
          <div className="tool-use">
            <span className="message-icon">{mapping.icon}</span>
            <div className="message-content">
              <span className="tool-text">{mapping.text}</span>
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

  const renderToolAction = (parameters) => {
    const action = parameters.action;
    const mapping = TOOL_ACTION_MAPPING[action] || { icon: '🔧', text: 'Performing action' };
    
    return (
      <div className="tool-action">
        <span className="tool-icon">{mapping.icon}</span>
        <span className="tool-text">{mapping.text}</span>
      </div>
    );
  };

  return (
    <div className={`chat-history-container ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="chat-header">
        <button 
          className="collapse-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? '▼' : '▲'}
        </button>
      </div>
      <div 
        ref={chatRef}
        className="chat-history"
      >
        {(isCollapsed ? getRecentMessages() : messages).map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            {renderMessage(msg)}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ChatHistory; 