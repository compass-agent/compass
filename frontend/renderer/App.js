import React, { useEffect, useRef, useState } from "react";
import { HashRouter as Router, Routes, Route } from "react-router-dom";
import "./main-chat/styles/common.scss";
import "./main-chat/styles/App.scss";
import ChatHistory from "./main-chat/components/ChatHistory";
import MessageInput from "./main-chat/components/MessageInput";
import ControlPanel from "./main-chat/components/ControlPanel";
import { AppProvider, useAppState } from "./common/context/AppContext";
import Header from "./main-chat/components/Header";
import useUpdateContainerHeight from "./main-chat/hooks/useUpdateContainerHeight";
import useScrollToBottom from "./main-chat/hooks/useScrollToBottom";
import { AgentStatus, AgentMode } from "./common/constants";

// Separate component for the main app content to use the context
function AppContent() {
  const { state } = useAppState();
  const { connection, chat, agent } = state;
  const chatHistoryRef = useRef(null); // Add a reference to the chat history wrapper
  const [editorWidth, setEditorWidth] = useState(0);
  // Use custom hooks
  useUpdateContainerHeight(chatHistoryRef);
  useScrollToBottom(chatHistoryRef, chat.messages);
  
  return (
    <div className="app">
      <div className="header-wrapper">
        <Header />
      </div>
      <div
        className="content"
         style={{ width: `calc(100% - ${editorWidth}px)` }}
      >
        {connection.error && (
          <div className="error-banner">{connection.error}</div>
        )}
        <div className="history-container">
          <div className="chat-history-wrapper" ref={chatHistoryRef}>
            <ChatHistory
              onEditorWidthChange={(newWidth) => {
              setEditorWidth(newWidth)
              }} // Callback to update editor width
            />
          </div>
          <div className="control-panel-wrapper">
            <ControlPanel />
          </div>
        </div>
        <div className="input-box-wrapper">
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
      <Router>
        <Routes>
          {/* Main App */}
          <Route path="/" element={<AppContent />} />
        </Routes>
      </Router>
    </AppProvider>
  );
}

export default App;
