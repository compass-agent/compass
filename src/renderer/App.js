import React, { useState, useEffect } from 'react';
import './App.css';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import ControlPanel from './components/ControlPanel';
import WebSocketService from './services/websocket';
import StateManager from './services/stateManager';

function App() {
  const [messages, setMessages] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({});

  useEffect(() => {
    // Subscribe to state changes
    const unsubscribeMessages = StateManager.subscribe('chat.messages', setMessages);
    const unsubscribeConnection = StateManager.subscribe('connection', setConnectionStatus);

    // Connect to WebSocket server
    WebSocketService.connect();

    // Cleanup on unmount
    return () => {
      unsubscribeMessages();
      unsubscribeConnection();
      WebSocketService.disconnect();
    };
  }, []);

  return (
    <div className="App">
      <div className="content">
        {connectionStatus.error && (
          <div className="error-banner">{connectionStatus.error}</div>
        )}
        <ChatHistory messages={messages} />
        <MessageInput 
          disabled={!connectionStatus.connected}
        />
        <ControlPanel />
      </div>
    </div>
  );
}

export default App;
