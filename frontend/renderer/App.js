import { faSpinner } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useRef, useState } from "react"
import { Route, HashRouter as Router, Routes } from "react-router-dom"
import { AgentMode, AgentStatus } from "./common/constants"
import { AppProvider, useAppState } from "./common/context/AppContext"
import ChatHistory from "./main-chat/components/ChatHistory"
import ControlPanel from "./main-chat/components/ControlPanel"
import Header from "./main-chat/components/Header"
import MessageInput from "./main-chat/components/MessageInput"
import useScrollToBottom from "./main-chat/hooks/useScrollToBottom"
import useUpdateContainerHeight from "./main-chat/hooks/useUpdateContainerHeight"
import "./main-chat/styles/App.scss"
import "./main-chat/styles/common.scss"

// Separate component for the main app content to use the context
function AppContent() {
  const { state } = useAppState()
  const { connection, chat, agent } = state
  const chatHistoryRef = useRef(null) // Add a reference to the chat history wrapper
  const [editorWidth, setEditorWidth] = useState(0)
  // Use custom hooks
  useUpdateContainerHeight(chatHistoryRef)
  useScrollToBottom(chatHistoryRef, chat.messages)
  const isAutoMode = agent.mode === AgentMode.AUTO
  const isMinimalView = isAutoMode && agent.status !== AgentStatus.STOPPED
  const isCompassReady = connection.connected //&& agent.status === AgentStatus.STOPPED

  useEffect(() => {
    if (window.electron.minimalWindow) {
      window.electron.minimalWindow(isMinimalView)
    }
  }, [isMinimalView])

  if (isMinimalView) {
    return (
      <div className="app" style={{ border: "2px solid rgb(145, 144, 144)" }}>
        <div className="control-panel-wrapper">
          <ControlPanel isMinimal={isMinimalView} />
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="header-wrapper">
        <Header />
      </div>
      <div
        className="content"
        style={{ width: `calc(100% - ${editorWidth}px)` }}
      >
        {!isCompassReady && (
          <div className="loading-spinner-container">
            <FontAwesomeIcon
              icon={faSpinner}
              spin
              size="3x"
              className="spinner-icon"
            />
            <div className="spinner-text">Connecting to Compass...</div>
          </div>
        )}
        {connection.error && (
          <div className="error-banner">{connection.error}</div>
        )}
        <div className="history-container">
          <div className="chat-history-wrapper" ref={chatHistoryRef}>
            <ChatHistory
              onEditorWidthChange={(newWidth) => {
                setEditorWidth(newWidth)
              }}
            />
          </div>
          <div
            className="control-panel-wrapper"
            style={{
              pointerEvents: isCompassReady ? "auto" : "none",
              opacity: isCompassReady ? 1 : 0.5,
            }}
          >
            <ControlPanel />
          </div>
        </div>
        <div
          className="input-box-wrapper"
          style={{
            pointerEvents: isCompassReady ? "auto" : "none",
            opacity: isCompassReady ? 1 : 0.5,
          }}
        >
          <MessageInput />
        </div>
      </div>
    </div>
  )
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
  )
}

export default App
