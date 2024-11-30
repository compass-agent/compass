import React from 'react';
import './styles/common.scss';
import './styles/App.scss';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';
import ControlPanel from './components/ControlPanel';
import { AppProvider, useAppState } from './context/AppContext';
import Header from './components/Header';

// Separate component for the main app content to use the context
function AppContent() {
  const { state } = useAppState();
  const { connection } = state;

  return (
    <div className="App">
      <Header />
      <div className="content">
        {connection.error && (
          <div className="error-banner">{connection.error}</div>
        )}
        <div className="chat-container">
          <ChatHistory />
        </div>
        <div className="bottom-controls">
          <div className="control-panel-wrapper">
            <ControlPanel />
          </div>
          <MessageInput />
        </div>
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
