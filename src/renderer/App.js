import React, { useState } from 'react';
import './App.css';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import ControlPanel from './components/ControlPanel';

function App() {
  const [messages, setMessages] = useState([]);

  const simulateResponse = async (userMessage) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    return `This is a simulated response to: "${userMessage}"`;
  };

  const handleSendMessage = async (message) => {
    // Add user message
    setMessages(prev => [...prev, { 
      type: 'user',
      text: message 
    }]);

    // Get and add AI response
    const response = await simulateResponse(message);
    setMessages(prev => [...prev, { 
      type: 'ai',
      text: response 
    }]);
  };

  return (
    <div className="App">
      <div className="content">
        <ChatHistory messages={messages} />
        <MessageInput onSendMessage={handleSendMessage} />
        <ControlPanel />
      </div>
    </div>
  );
}

export default App;
