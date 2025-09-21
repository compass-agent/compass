import React, { useEffect, useState } from "react"
import WebSocketService from "../common/services/websocket"
import AgentHub from "./components/AgentHub"
import AgentSetup from "./components/AgentSetup"
import PageEditor from "./components/PageEditor"
import PagesList from "./components/PagesList"
import Settings from "./components/Settings"
import { VIEW_STATES } from "./constants/viewStates"
import { useBoxManagement } from "./hooks/useBoxManagement"
import AgentHubService from "./services/agentHubService"
import "./styles/TemplateTraining.scss"

console.log("TemplateTraining component is rendering")

const TemplateTraining = () => {
  const [currentView, setCurrentView] = useState(VIEW_STATES.AGENT_HUB)
  const [selectedAgentId, setSelectedAgentId] = useState(
    "structural-engineer-default"
  )
  const [agentData, setAgentData] = useState({
    agentId: "structural-engineer-default",
    name: "Structural-Engineer",
    description:
      "Structural analysis expert for engineering calculations and design",
    prompt:
      "You are an expert structural engineer assistant specialized in SAP2000, structural analysis, modeling, and design tasks.",
    generalTools: [
      { id: 'fileEditor', name: 'File Editor', config: { rootDir: '', restricted: true } }
    ],
    softwareIntegrations: [
      { id: 'SAP2000', name: 'SAP2000', scripting: true, desktop: true, config: {}, trainingStatus: 'configured' }
    ],
    configuration: {},
    pages: [],
  })
  const [saveStatus, setSaveStatus] = useState("")
  const [inputValue, setInputValue] = useState("")
  const [currentScreenshot, setCurrentScreenshot] = useState(null)
  const [pageName, setPageName] = useState("")

  // Template training state (moved from useSocketConnection)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [detections, setDetections] = useState([])

  // Custom hooks
  const {
    boxes,
    setBoxes,
    selectedBox,
    setSelectedBox,
    captions,
    setCaptions,
    handleBoxClick,
    handleDragStop,
    createNewBox,
    deleteBox,
  } = useBoxManagement(detections)

  // Setup cleanup functions for image handling
  const cleanupFunctions = {
    setDetections,
    setBoxes,
    setCaptions,
    setSelectedBox,
    setIsAnalyzing,
  }

  // Update input value when selecting a box
  useEffect(() => {
    if (selectedBox !== null && captions[selectedBox]) {
      setInputValue(captions[selectedBox])
    } else {
      setInputValue("")
    }
  }, [selectedBox, captions])

  // Update pageName when currentScreenshot changes
  useEffect(() => {
    if (currentScreenshot) {
      // Backend returns screenshot with 'name' property
      const name = currentScreenshot.name || ""
      setPageName(name)
    } else {
      setPageName("")
    }
  }, [currentScreenshot])

  // WebSocket handlers setup
  useEffect(() => {
    // Set up template training specific handler
    const handleDetectionResult = (data) => {
      console.log("🎯 Detection result received:", data)
      if (data && data.detections) {
        setDetections(data.detections)
      } else {
        console.error("❌ Invalid detection result format:", data)
        setDetections([])
      }
      setIsAnalyzing(false)
    }

    // Store previous handler
    const prevHandler = WebSocketService.stateHandlers.onDetectionResult

    // Set our handler
    WebSocketService.stateHandlers.onDetectionResult = handleDetectionResult

    // Set up templates saved handler
    WebSocketService.stateHandlers.onTemplatesSaved = (data) => {
      if (data.success) {
        setSaveStatus("Templates saved successfully!")
        setTimeout(() => setSaveStatus(""), 3000)
      } else {
        setSaveStatus("Error saving templates")
      }
    }

    return () => {
      // Restore previous handler
      WebSocketService.stateHandlers.onDetectionResult = prevHandler
    }
  }, [])

  // Auto-send default agent data to main window on mount
  useEffect(() => {
    // Send default agent data to main window when component mounts
    if (window.electron?.ipcRenderer?.invoke) {
      const defaultAgentData = {
        agentId: "structural-engineer-default",
        name: "Structural-Engineer",
        description:
          "Structural analysis expert for engineering calculations and design",
        prompt:
          "You are an expert structural engineer assistant specialized in SAP2000, structural analysis, modeling, and design tasks.",
        generalTools: [
          { id: 'fileEditor', name: 'File Editor', config: { rootDir: '', restricted: true } }
        ],
        softwareIntegrations: [
          { id: 'SAP2000', name: 'SAP2000', scripting: true, desktop: true, config: {}, trainingStatus: 'configured' }
        ],
        configuration: {},
      }

      console.log(
        "🚀 Auto-sending default agent data to main window:",
        defaultAgentData
      )

      window.electron.ipcRenderer
        .invoke("agent-selected", defaultAgentData)
        .then((result) => {
          console.log("🚀 Auto-send result:", result)
        })
        .catch((error) => {
          console.error("🚀 Auto-send error:", error)
        })
    }
  }, [])

  // Set default agent data when Agent Hub is first displayed
  useEffect(() => {
    if (
      currentView === VIEW_STATES.AGENT_HUB &&
      agentData.agentId === "structural-engineer-default"
    ) {
      // This ensures the default agent is properly set when Agent Hub is first shown
      console.log("🎯 Agent Hub displayed, default agent data is set")
    }
  }, [currentView, agentData.agentId])

  const handleAnalyze = (imageData) => {
    if (!imageData) {
      alert("Please upload an image first")
      return
    }
    console.log(
      "🔍 handleAnalyze called with imageData:",
      imageData ? "present" : "missing"
    )
    console.log("🔍 agentData.name:", agentData.name)
    console.log(
      "🔍 WebSocketService.socket?.connected:",
      WebSocketService.socket?.connected
    )

    setIsAnalyzing(true)

    const base64Image = imageData.split(",")[1] || imageData
    console.log("🔍 About to call WebSocketService.uploadScreenshot")
    WebSocketService.uploadScreenshot(base64Image, agentData.name)
  }

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && selectedBox !== null) {
      setCaptions((prev) => ({
        ...prev,
        [selectedBox]: inputValue,
      }))
      setSelectedBox(null)
      setInputValue("")
    }
  }

  const handleNavigate = (view) => {
    // Clear currentScreenshot when navigating to PAGES_LIST
    if (view === VIEW_STATES.PAGES_LIST) {
      setCurrentScreenshot(null)
    }

    // Clear template state when navigating away from PAGE_EDITOR
    if (
      currentView === VIEW_STATES.PAGE_EDITOR &&
      view !== VIEW_STATES.PAGE_EDITOR
    ) {
      console.log("🧹 Clearing template state when leaving PageEditor")
      setDetections([])
      setBoxes({})
      setCaptions({})
      setSelectedBox(null)
      setIsAnalyzing(false)
      setInputValue("")
    }

    setCurrentView(view)
  }

  const getPageTitle = () => {
    switch (currentView) {
      case VIEW_STATES.SETUP:
        return agentData.agentId ? "Edit Agent" : "Create New Agent"
      default:
        return null // Let TemplateNavigation handle default titles
    }
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case VIEW_STATES.AGENT_HUB:
        return (
          <AgentHub
            selectedAgentId={selectedAgentId}
            onAgentSelect={(agent) => {
              console.log(
                "🎯 Agent selected in TemplateTraining:",
                agent.name,
                "ID:",
                agent.agentId
              )
              setSelectedAgentId(agent.agentId)

              // Send selected agent to main window
              if (window.electron?.ipcRenderer?.invoke) {
                const agentDataToSend = {
                  agentId: agent.agentId,
                  name: agent.name,
                  description: agent.description,
                  generalTools: agent.generalTools,
                  softwareIntegrations: agent.softwareIntegrations,
                  configuration: agent.configuration,
                }
                console.log("🚀 Sending agent data via IPC:", agentDataToSend)

                window.electron.ipcRenderer
                  .invoke("agent-selected", agentDataToSend)
                  .then((result) => {
                    console.log("🚀 IPC invoke result:", result)
                    if (!result.success) {
                      console.error("🚀 IPC invoke failed:", result.error)
                    }
                  })
                  .catch((error) => {
                    console.error("🚀 IPC invoke error:", error)
                  })
              } else {
                console.error("🚀 IPC renderer not available")
              }
            }}
            onSelectAgent={(agentNameOrData) => {
              if (agentNameOrData) {
                if (typeof agentNameOrData === "string") {
                  // Legacy: just agent name, need to find full agent data
                  // For now, set minimal data - should be updated to pass full agent object
                  setAgentData((prev) => ({
                    ...prev,
                    name: agentNameOrData,
                    agentId: null,
                  }))
                } else {
                  // Full agent object passed
                  setAgentData({
                    agentId: agentNameOrData.agentId,
                    name: agentNameOrData.name,
                    description: agentNameOrData.description || "",
                    prompt: agentNameOrData.prompt || "",
                    generalTools: agentNameOrData.generalTools || [],
                    softwareIntegrations: agentNameOrData.softwareIntegrations || [],
                    configuration: agentNameOrData.configuration || {},
                    pages: [],
                  })
                }
              } else {
                // Creating new agent - clear agent data
                setAgentData({
                  agentId: null,
                  name: "",
                  description: "",
                  prompt: "",
                  generalTools: [],
                  softwareIntegrations: [],
                  configuration: {},
                  pages: [],
                })
              }
              setCurrentView(VIEW_STATES.SETUP)
            }}
            onCreateNew={() => setCurrentView(VIEW_STATES.SETUP)}
          />
        )
      case VIEW_STATES.SETUP:
        return (
          <AgentSetup
            existingAgent={agentData.agentId ? agentData : null}
            onNext={(agentInfo) => {
              const updatedAgentData = {
                ...agentData,
                name: agentInfo.name,
                description: agentInfo.description,
                prompt: agentInfo.prompt,
                generalTools: agentInfo.generalTools,
                softwareIntegrations: agentInfo.softwareIntegrations,
                configuration: agentInfo.configuration,
              }

              setAgentData(updatedAgentData)

              // Send updated agent data to main window via IPC
              if (window.electron?.ipcRenderer?.invoke) {
                const agentDataToSend = {
                  agentId: updatedAgentData.agentId,
                  name: updatedAgentData.name,
                  description: updatedAgentData.description,
                  generalTools: updatedAgentData.generalTools,
                  softwareIntegrations: updatedAgentData.softwareIntegrations,
                  configuration: updatedAgentData.configuration,
                }
                console.log(
                  "🚀 Sending updated agent data via IPC:",
                  agentDataToSend
                )

                window.electron.ipcRenderer
                  .invoke("agent-selected", agentDataToSend)
                  .then((result) => {
                    console.log(
                      "🚀 IPC invoke result for updated agent:",
                      result
                    )
                    if (!result.success) {
                      console.error(
                        "🚀 IPC invoke failed for updated agent:",
                        result.error
                      )
                    }
                  })
                  .catch((error) => {
                    console.error(
                      "🚀 IPC invoke error for updated agent:",
                      error
                    )
                  })
              } else {
                console.error("🚀 IPC renderer not available for updated agent")
              }

              // Determine if we're creating or updating
              if (agentData.agentId) {
                // Updating existing agent
                AgentHubService.updateAgent(agentData.agentId, updatedAgentData)
              } else {
                // Creating new agent
                AgentHubService.createAgent(updatedAgentData)
              }

              setCurrentView(VIEW_STATES.AGENT_HUB)
            }}
            onTrainUI={(agentInfo) => {
              const updatedAgentData = {
                ...agentData,
                name: agentInfo.name,
                description: agentInfo.description,
                prompt: agentInfo.prompt,
                generalTools: agentInfo.generalTools,
                softwareIntegrations: agentInfo.softwareIntegrations,
                configuration: agentInfo.configuration,
              }

              setAgentData(updatedAgentData)

              // Send updated agent data to main window via IPC
              if (window.electron?.ipcRenderer?.invoke) {
                const agentDataToSend = {
                  agentId: updatedAgentData.agentId,
                  name: updatedAgentData.name,
                  description: updatedAgentData.description,
                  generalTools: updatedAgentData.generalTools,
                  softwareIntegrations: updatedAgentData.softwareIntegrations,
                  configuration: updatedAgentData.configuration,
                }
                console.log(
                  "🚀 Sending updated agent data via IPC (Train UI):",
                  agentDataToSend
                )
                console.log(
                  "🚀 Updated agent tools being sent (Train UI):",
                  agentDataToSend.tools
                )

                window.electron.ipcRenderer
                  .invoke("agent-selected", agentDataToSend)
                  .then((result) => {
                    console.log(
                      "🚀 IPC invoke result for updated agent (Train UI):",
                      result
                    )
                    if (!result.success) {
                      console.error(
                        "🚀 IPC invoke failed for updated agent (Train UI):",
                        result.error
                      )
                    }
                  })
                  .catch((error) => {
                    console.error(
                      "🚀 IPC invoke error for updated agent (Train UI):",
                      error
                    )
                  })
              } else {
                console.error(
                  "🚀 IPC renderer not available for updated agent (Train UI)"
                )
              }

              // Save the agent first (create or update)
              if (agentData.agentId) {
                // Updating existing agent
                AgentHubService.updateAgent(agentData.agentId, agentInfo)
              } else {
                // Creating new agent
                AgentHubService.createAgent(agentInfo)
              }

              // Navigate to template training (pages list)
              setCurrentView(VIEW_STATES.PAGES_LIST)
            }}
          />
        )
      case VIEW_STATES.PAGES_LIST:
        return (
          <PagesList
            agentName={agentData.name}
            onAddPage={() => {
              // Clear template state when creating new page
              console.log("🧹 Clearing template state when creating new page")
              setDetections([])
              setBoxes({})
              setCaptions({})
              setSelectedBox(null)
              setIsAnalyzing(false)
              setInputValue("")

              setCurrentScreenshot(null)
              setCurrentView(VIEW_STATES.PAGE_EDITOR)
            }}
            onEditPage={(screenshot) => {
              // Clear template state when opening a different page
              console.log(
                "🧹 Clearing template state when opening different page"
              )
              setDetections([])
              setBoxes({})
              setCaptions({})
              setSelectedBox(null)
              setIsAnalyzing(false)
              setInputValue("")

              setCurrentScreenshot(screenshot)
              setCurrentView(VIEW_STATES.PAGE_EDITOR)
            }}
          />
        )
      case VIEW_STATES.PAGE_EDITOR:
        return (
          <PageEditor
            onSave={(pageData) => {
              setAgentData((prev) => ({
                ...prev,
                pages: [...prev.pages, pageData],
              }))
              setPageName(pageData.name || "")
              setCurrentView(VIEW_STATES.PAGES_LIST)
            }}
            onCancel={() => {
              // Clear template state when canceling
              console.log("🧹 Clearing template state when canceling")
              setDetections([])
              setBoxes({})
              setCaptions({})
              setSelectedBox(null)
              setIsAnalyzing(false)
              setInputValue("")

              setCurrentScreenshot(null)
              setCurrentView(VIEW_STATES.PAGES_LIST)
            }}
            handleAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
            boxes={boxes}
            selectedBox={selectedBox}
            handleBoxClick={handleBoxClick}
            createNewBox={createNewBox}
            deleteBox={deleteBox}
            inputValue={inputValue}
            setInputValue={setInputValue}
            handleKeyPress={handleKeyPress}
            captions={captions}
            setCurrentView={setCurrentView}
            setDetections={setDetections}
            setBoxes={setBoxes}
            setCaptions={setCaptions}
            setSelectedBox={setSelectedBox}
            setIsAnalyzing={setIsAnalyzing}
            currentScreenshot={currentScreenshot}
            agentName={agentData.name}
            pageName={pageName}
            setPageName={setPageName}
          />
        )
      case VIEW_STATES.SETTINGS:
        return <Settings onNavigate={setCurrentView} />
      default:
        return null
    }
  }

  // Custom title bar component with integrated navigation
  const CustomTitleBar = () => {
    const renderBreadcrumb = () => {
      // For SETTINGS view, just show Settings
      if (currentView === VIEW_STATES.SETTINGS) {
        return <span className="nav-text">Settings</span>
      }

      // For AGENT_HUB view, just show Agent Hub
      if (currentView === VIEW_STATES.AGENT_HUB) {
        return <span className="nav-text">Agent Hub</span>
      }

      // For other views, show navigation breadcrumb
      const items = []

      // Agent Hub (clickable to go back)
      items.push(
        <span
          key="hub"
          className="nav-item"
          onClick={() => handleNavigate(VIEW_STATES.AGENT_HUB)}
        >
          Agent Hub
        </span>
      )

      // Add separator and next level
      if (currentView !== VIEW_STATES.AGENT_HUB) {
        items.push(
          <span key="sep1" className="nav-separator">
            ›
          </span>
        )

        // Determine the current page label and navigation
        if (currentView === VIEW_STATES.SETUP) {
          const isCreating = getPageTitle() === "Create New Agent"
          const currentLabel = isCreating
            ? `Create ${agentData.name || "Agent"}`
            : `Edit ${agentData.name || "Agent"}`
          items.push(
            <span key="current" className="nav-text">
              {currentLabel}
            </span>
          )
        } else if (currentView === VIEW_STATES.PAGES_LIST) {
          // Agent Hub > Edit Agent > Pages
          items.push(
            <span
              key="setup"
              className="nav-item"
              onClick={() => handleNavigate(VIEW_STATES.SETUP)}
            >
              Edit {agentData.name || "Agent"}
            </span>
          )
          items.push(
            <span key="sep2" className="nav-separator">
              ›
            </span>
          )
          items.push(
            <span key="pages" className="nav-text">
              Pages
            </span>
          )
        } else if (currentView === VIEW_STATES.PAGE_EDITOR) {
          // Agent Hub > Edit Agent > Pages > Page Name
          items.push(
            <span
              key="setup"
              className="nav-item"
              onClick={() => handleNavigate(VIEW_STATES.SETUP)}
            >
              Edit {agentData.name || "Agent"}
            </span>
          )
          items.push(
            <span key="sep2" className="nav-separator">
              ›
            </span>
          )
          items.push(
            <span
              key="pages"
              className="nav-item"
              onClick={() => handleNavigate(VIEW_STATES.PAGES_LIST)}
            >
              Pages
            </span>
          )
          items.push(
            <span key="sep3" className="nav-separator">
              ›
            </span>
          )
          items.push(
            <span key="page" className="nav-text">
              {pageName || "New Page"}
            </span>
          )
        }
      }

      return items
    }

    return (
      <div className="custom-title-bar">
        <div className="title-bar-content">
          <div className="title-breadcrumb">{renderBreadcrumb()}</div>
        </div>
        <div className="title-bar-controls">
          <button
            className="title-control close"
            onClick={() => {
              // Close only this window, not the main app
              if (window.electron?.ipcRenderer?.send) {
                window.electron.ipcRenderer.send("close-template-training")
              }
            }}
          >
            ✕
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="template-training">
      <CustomTitleBar />
      {saveStatus && (
        <div
          className={`save-status ${
            saveStatus.includes("Error") ? "error" : "success"
          }`}
        >
          {saveStatus}
        </div>
      )}
      <div className="content">{renderCurrentView()}</div>
    </div>
  )
}

export default TemplateTraining
