import React, { useRef, useState, useEffect } from 'react';
import { useAppState } from '../context/AppContext';
import '../styles/ChatHistory.scss';
import { MESSAGE_TYPES } from '../constants';
import { faSpinner  } from '@fortawesome/free-solid-svg-icons';
import { AgentStatus } from '../constants';

const TOOL_ACTION_MAPPING = {
  screenshot: { icon: '📸', text: 'Taking screenshot...' },
  click: { icon: '🖱️', text: 'Clicking element' },
  type: { icon: '⌨️', text: 'Typing text' },
  // Add more mappings as needed
};

function ChatHistory() {
  const { state } = useAppState();
  const { messages } = state.chat;
  const { agent: agenStatus } = state;
  const chatRef = useRef(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  // TODO: Issue: this state is defined locally. to be able use it in chatInput.js,
  // it should be defined in the context or common parent component (AppContent)
  console.log('ChatHistory - Current messages:', messages);
  // Add scroll to bottom effect: as the new chat is added
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [state.chat.messages, streamingText]);

  // Update streaming text handling
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.type === 'ai_response_stream') {
        if (lastMessage.is_final) {
          setStreamingText('');
        } else {
          setStreamingText(prev => prev + lastMessage.content);
        }
      }
    }
  }, [messages]);

  // Add the missing getRecentMessages function
  const getRecentMessages = () => {
    if (!messages.length) return [];
    
    // Find the index of the most recent AI response
    const lastAiIndex = [...messages].reverse().findIndex(msg => msg.type === MESSAGE_TYPES.AI_RESPONSE);
    
    if (lastAiIndex === -1) {
      // If no AI response found, return just the last message
      return messages.slice(-1);
    }
    
    // Return the AI response and all subsequent messages
    return messages.slice(-(lastAiIndex + 1));
  };

  const renderMessage = (msg, agenStatus) => {
    console.log('Rendering message:', msg, agenStatus.autoMode);
    console.log('Rendering type:', MESSAGE_TYPES.USER, MESSAGE_TYPES.USER === msg.type);
    switch (msg.type) {
      case MESSAGE_TYPES.USER:
        if (!msg.text) {
          return null;
      }
        return (
          // user-message
          <div className="message user-message">
            {/* <span className="message-icon">👤</span> */}
            {/* <FontAwesomeIcon icon={faSpinner}  spin  /> */}
            <div className="message-content copyable-text" title={ (agenStatus.autoMode && agenStatus.status !== AgentStatus.STOPPED) ? msg.text : ''}>
              {msg.text}
            </div>
          </div>
        );

      case MESSAGE_TYPES.AI_RESPONSE:
        if (!msg.content) {
          return null;
        }
        return (
          <div className="message">
            <div className="message-content copyable-text" title={agenStatus.autoMode && agenStatus.status !== AgentStatus.STOPPED ? msg.content : ''}>
              {msg.content}
            </div>
          </div>
        );
      
      case MESSAGE_TYPES.AI_RESPONSE_STREAM:
        // Don't render individual stream messages
        return null;
      
      case MESSAGE_TYPES.TOOL_USE:
        const action = msg.parameters?.action;
        const mapping = TOOL_ACTION_MAPPING[action] || { icon: '🔧', text: 'Performing action ...' };
        if (!mapping.text) {
          return null;
      }
        return (
          //tool-use
          <div className="message">
            {/* <span className="message-icon">{mapping.icon}</span> */}
            {/* <FontAwesomeIcon icon={faSpinner}  spin  /> */}
            <div className="message-content copyable-text">
              {/* why tool-text? */}
              <span className="tool-text" title={ agenStatus.autoMode && agenStatus.status !== AgentStatus.STOPPED ? mapping.text : ''}>{mapping.text}</span>
            </div>
          </div>
        );
      
      case MESSAGE_TYPES.TOOL_RESULT:
        if (!msg.error && !msg.output) {
          return null;
      }
        return (
          //tool-result
          <div className="message">
            {/* <span className="message-icon">📊</span> */}
            {/* <FontAwesomeIcon icon={faSpinner}  spin  /> */}
            <div className="message-content copyable-text">
              {msg.error ? (
                <div className="tool-error" title={ agenStatus.autoMode && agenStatus.status !== AgentStatus.STOPPED ? msg.error : ''}>{msg.error}</div>
              ) : (
                <>
                  {msg.output && <div className="tool-output" title={ agenStatus.autoMode && agenStatus.status !== AgentStatus.STOPPED ? msg.output : ''}>{msg.output}</div>}
                  {msg.has_image && <div className="tool-image-placeholder">[Image]</div>}
                </>
              )}
            </div>
          </div>
        );
      
      default:
        return (
          <div className="message-content copyable-text" title={agenStatus.autoMode && agenStatus.status !== AgentStatus.STOPPED ? msg.text : ''}>
            {msg.text}
          </div>
        );
    }
  };
//TODO KAZEM => Is there any Usage?
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
    //isCollapsed is not applied yet
    <div className='chat-history-container'>
      {/* <div className="chat-header">
        <button 
          className="collapse-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? '▼' : '▲'}
        </button>
      </div> */}
      <div 
        ref={chatRef}
        className="chat-history"
      >
        {(isCollapsed ? getRecentMessages() : messages).map((msg, index) => (
          <React.Fragment key={index}>
          {renderMessage(msg, agenStatus)}
        </React.Fragment>
        ))}
        {/* Add streaming text display */}
        {streamingText && (
          <div className="message">
            <div className="message-content copyable-text">
              {streamingText}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatHistory; 