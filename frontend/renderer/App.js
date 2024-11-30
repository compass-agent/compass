import React from 'react';
import './App.css';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import ControlPanel from './components/ControlPanel';
import { AppProvider, useAppState } from './context/AppContext';

// Separate component for the main app content to use the context
function AppContent() {
  const { state } = useAppState();
  const { connection } = state;

  return (
    <div className="App">
      <div className="content">
        {connection.error && (
          <div className="error-banner">{connection.error}</div>
        )}
        <ChatHistory />
        <MessageInput 
          disabled={!connection.connected}
        />
        <ControlPanel />
      </div>
    </div>
  );
}

// Main App component wrapped with the provider
function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
