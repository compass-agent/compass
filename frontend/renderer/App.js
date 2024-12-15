import React, { useEffect, useRef } from "react";
import "./styles/common.scss";
import "./styles/App.scss";
import ChatHistory from "./components/ChatHistory";
import MessageInput from "./components/MessageInput";
import ControlPanel from "./components/ControlPanel";
import { AppProvider, useAppState } from "./context/AppContext";
import Header from "./components/Header";
import useUpdateContainerHeight from "./hooks/useUpdateContainerHeight";
import useScrollToBottom from "./hooks/useScrollToBottom";

// Separate component for the main app content to use the context
function AppContent() {
  const { state } = useAppState();
  const { connection, chat, agent: agentState } = state;
  const chatHistoryRef = useRef(null); // Add a reference to the chat history wrapper

  // Use custom hooks
  useUpdateContainerHeight(chatHistoryRef);
  useScrollToBottom(chatHistoryRef, chat.messages);

  return (
    <div className="app">
      <div className="header-wrapper">
        <Header />
      </div>
      <div className="content">
        {connection.error && (
          <div className="error-banner">{connection.error}</div>
        )}
        <div className="history-container">
          <div className="chat-history-wrapper" ref={chatHistoryRef}>
            <ChatHistory />
          </div>
          <div className="control-panel-wrapper">
            <ControlPanel />
          </div>
        </div>
        <div className="input-box-wrapper" style={{ display: agentState.autoMode ? 'none' : 'block' }}>
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
