import React, { useState, useEffect } from 'react';
import './App.css';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import ControlPanel from './components/ControlPanel';
import WebSocketService from './services/websocket';
import StateManager from './services/stateManager';
import MessageHandler from './services/messageHandler';

function App() {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({});

  useEffect(() => {
    // Subscribe to state changes
    const unsubscribeMessages = StateManager.subscribe('chat.messages', setMessages);
    const unsubscribeConnection = StateManager.subscribe('connection', setConnectionStatus);

    // Connect to WebSocket server
    WebSocketService.connect();

    // Set up message handlers
    WebSocketService.onMessage('response', (response) => {
      MessageHandler.handleIncomingMessage(response);
    });

    // Cleanup on unmount
    return () => {
      unsubscribeMessages();
      unsubscribeConnection();
      WebSocketService.disconnect();
    };
  }, []);

  const handleSendMessage = async (message) => {
    // Add user message to state
    StateManager.setState('chat.messages', [...messages, { 
      type: 'user',
      text: message 
    }]);

    // Queue message for sending
    await MessageHandler.queueOutgoingMessage(message);
  };

  return (
    <div className="App">
      <div className="content">
        {connectionStatus.error && (
          <div className="error-banner">{connectionStatus.error}</div>
        )}
        <ChatHistory messages={messages} />
        <MessageInput 
          onSendMessage={handleSendMessage} 
          disabled={!connectionStatus.isConnected}
        />
        <ControlPanel />
      </div>
    </div>
  );
}

export default App;
