import React, { useEffect, useRef, useState } from "react"
import { Route, HashRouter as Router, Routes } from "react-router-dom"
import { AgentMode } from "./common/constants"
import { AppProvider, useAppState } from "./common/context/AppContext"
import ChatHistory from "./main-chat/components/ChatHistory"
import ControlPanel from "./main-chat/components/ControlPanel"
import Header from "./main-chat/components/Header"
import MessageInput from "./main-chat/components/MessageInput"
import SettingsModal from "./main-chat/components/SettingsModal"
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
  const isMinimalView = false // isAutoMode && agent.status !== AgentStatus.STOPPED
  const isCompassReady = connection.connected //&& agent.status === AgentStatus.STOPPED

  // Settings / first-run onboarding
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [isFirstRun, setIsFirstRun] = useState(false)

  useEffect(() => {
    // Open onboarding automatically when no Anthropic key is configured yet
    if (window.electron?.settings?.get) {
      window.electron.settings
        .get()
        .then((s) => {
          if (!s.onboardingCompleted) {
            setIsFirstRun(true)
            setSettingsOpen(true)
          }
        })
        .catch(() => {})
    }

    // Allow other components (e.g. the Header gear icon) to open settings
    const openSettings = () => {
      setIsFirstRun(false)
      setSettingsOpen(true)
    }
    window.addEventListener("open-compass-settings", openSettings)
    return () =>
      window.removeEventListener("open-compass-settings", openSettings)
  }, [])

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
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        isFirstRun={isFirstRun}
        connected={connection.connected}
      />
      <div className="header-wrapper">
        <Header />
      </div>
      <div
        className="content"
        style={{ width: `calc(100% - ${editorWidth}px)` }}
      >
        {!isCompassReady && (
          <div className="loading-spinner-container">
            <svg
              className="compass-loading-mark"
              viewBox="0 0 100 100"
              aria-hidden="true"
            >
              <circle
                className="compass-loading-ring"
                cx="50"
                cy="50"
                r="28"
              />
              <g className="compass-loading-orbit">
                <circle
                  className="compass-loading-dot"
                  cx="72"
                  cy="28"
                  r="8"
                />
              </g>
            </svg>
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
        </div>
        <div
          className="input-box-wrapper"
          style={{
            pointerEvents: isCompassReady ? "auto" : "none",
            opacity: isCompassReady ? 1 : 0.5,
          }}
        >
          <MessageInput />
          <div className="control-panel-wrapper">
            <ControlPanel />
          </div>
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
