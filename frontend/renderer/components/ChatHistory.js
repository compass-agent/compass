import React, { useRef, useState, useEffect } from 'react';
import { useAppState } from '../context/AppContext';
import '../styles/ChatHistory.scss';
import { MESSAGE_TYPES } from '../constants';
import { faSpinner  } from '@fortawesome/free-solid-svg-icons';
import { AgentStatus, AgentMode } from '../constants';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faTimes, faClock } from '@fortawesome/free-solid-svg-icons';
import { TOOL_ACTION_MAPPING } from '../constants/toolActionMappings';
import CoordinatePreview from './preview/components/CoordinatePreview';

function ChatHistory() {
  const { state } = useAppState();
  const { messages } = state.chat;
  const { agent: agentState } = state;
  const chatRef = useRef(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const isAutoMode = agentState.mode === AgentMode.AUTO;
  const [toolResults, setToolResults] = useState(new Map()); // Store tool results by ID
  const [expandedTools, setExpandedTools] = useState(new Set());
  const [previewCoord, setPreviewCoord] = useState({ x: 0, y: 0, visible: false });
  // TODO: Issue: this state is defined locally. to be able use it in chatInput.js,
  // it should be defined in the context or common parent component (AppContent)
  // console.log('ChatHistory - Current messages:', messages);
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

  // Add logging to tool results effect
  useEffect(() => {
    console.log('Tool Results Effect - Current toolResults:', toolResults);
    console.log('Tool Results Effect - Processing messages:', messages);
    
    const newToolResults = new Map(toolResults);
    messages.forEach(msg => {
      console.log('Processing message:', msg);
      if (msg.type === MESSAGE_TYPES.TOOL_RESULT) {
        console.log('Raw tool result message:', msg);
        console.log('Tool result content:', msg.content);
        console.log('Tool use ID:', msg.toolUseId);
        
        if (msg.toolUseId) {
          console.log('Setting tool result for ID:', msg.toolUseId);
          newToolResults.set(msg.toolUseId, {
            isError: msg.isError,
            result: msg.content
          });
        } else {
          console.warn('Tool result message missing toolUseId:', msg);
        }
      }
    });
    
    if (newToolResults.size !== toolResults.size) {
      console.log('Updating tool results:', Object.fromEntries(newToolResults));
      setToolResults(newToolResults);
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

  const toggleToolExpansion = (toolId) => {
    setExpandedTools(prev => {
      const newSet = new Set(prev);
      if (newSet.has(toolId)) {
        newSet.delete(toolId);
      } else {
        newSet.add(toolId);
      }
      return newSet;
    });
  };

  const handleFileClick = (filePath) => {
    // Send IPC message to main process to open file
    window.electron.ipcRenderer.send('open-file', filePath);
  };

  const renderToolUse = (tool) => {
    console.log('renderToolUse - Received tool:', tool);
    
    const toolId = tool.id;
    const toolResult = toolResults.get(toolId);
    const isExpanded = expandedTools.has(toolId);
    
    const action = tool.input?.action || tool.name;
    console.log('renderToolUse - Looking up action in TOOL_ACTION_MAPPING:', action);
    
    const toolInfo = TOOL_ACTION_MAPPING[action] || { 
      label: 'Unknown Action',
      description: () => 'Performing action'
    };

    const labelContent = typeof toolInfo.label === 'function' 
      ? toolInfo.label(tool)
      : toolInfo.label;

    const description = toolInfo.description(tool);
    const hasExpandableContent = description && (
      description.text || 
      description.component || 
      (typeof description === 'string' && description.length > 0)
    );
    
    return (
      <div className="tool-suggestion">
        <div 
          className="tool-header" 
          onClick={() => hasExpandableContent && toggleToolExpansion(toolId)}
          style={{ cursor: hasExpandableContent ? 'pointer' : 'default' }}
        >
          <div className="tool-header-content">
            {hasExpandableContent && (
              <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
            )}
            <span className="tool-label" onClick={(e) => {
              // Prevent expansion toggle when clicking the file link
              if (e.target.classList.contains('file-link')) {
                e.stopPropagation();
                handleFileClick(tool.input.path);
              }
            }}>
              {labelContent}
            </span>
          </div>
          <span className="tool-status">
            {toolResult ? (
              toolResult.isError ? (
                <FontAwesomeIcon icon={faTimes} className="error" />
              ) : (
                <FontAwesomeIcon icon={faCheck} className="success" />
              )
            ) : (
              <FontAwesomeIcon icon={faClock} className="pending" />
            )}
          </span>
        </div>
        {isExpanded && hasExpandableContent && (
          <div className="tool-details">
            <div className="tool-input-value">
              {typeof description === 'object' ? (
                <>
                  {description.text}
                  {description.component}
                </>
              ) : (
                description
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderMessage = (msg, agentState) => {
    console.log('renderMessage - Full message object:', msg);
    
    switch (msg.type) {
      case MESSAGE_TYPES.USER:
        if (!msg.text) return null;
        return (
          <div className="message user-message">
            <div className="message-content copyable-text" title={(isAutoMode && agentState.status !== AgentStatus.STOPPED) ? msg.text : ''}>
              {msg.text}
            </div>
          </div>
        );

      case MESSAGE_TYPES.AI_RESPONSE:
        if (!msg.content) return null;
        return (
          <div className="message">
            <div className="message-content copyable-text">
              {msg.content}
            </div>
          </div>
        );
      
      case MESSAGE_TYPES.AI_RESPONSE_STREAM:
        // Don't render individual stream messages
        return null;
      
      case MESSAGE_TYPES.TOOL_RESULT:
        // Don't render tool results as separate messages
        return null;
      
      case MESSAGE_TYPES.TOOL_USE_GROUP:
        console.log('renderMessage - Processing tool_use_group:', {
          tools: msg.tools,
          content: msg.content
        });
        return (
          <div className="tool-suggestion-group">
            {(msg.tools || []).map((tool, index) => (
              <React.Fragment key={tool.id || index}>
                {renderToolUse(tool)}
              </React.Fragment>
            ))}
          </div>
        );
      
      default:
        return (
          <div className="message-content copyable-text" title={isAutoMode && agentState.status !== AgentStatus.STOPPED ? msg.text : ''}>
            {msg.text}
          </div>
        );
    }
  };

  return (
    <div className='chat-history-container'>
      <div ref={chatRef} className="chat-history">
        {(isCollapsed ? getRecentMessages() : messages).map((msg, index) => (
          <React.Fragment key={index}>
          {renderMessage(msg, agentState)}
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
      {previewCoord.visible && (
        <CoordinatePreview 
          x={previewCoord.x}
          y={previewCoord.y}
          visible={true}
        />
      )}
    </div>
  );
}

export default ChatHistory; 