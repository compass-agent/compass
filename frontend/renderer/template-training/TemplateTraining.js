import React, { useEffect, useState } from "react"
import WebSocketService from "../common/services/websocket"
import AgentHub from "./components/AgentHub"
import AgentSetup from "./components/AgentSetup"
import PageEditor from "./components/PageEditor"
import PagesList from "./components/PagesList"
import Settings from "./components/Settings"
import TemplateNavigation from "./components/TemplateNavigation"
import { VIEW_STATES } from "./constants/viewStates"
import { useBoxManagement } from "./hooks/useBoxManagement"
import AgentHubService from "./services/agentHubService"
import "./styles/TemplateTraining.scss"

console.log("TemplateTraining component is rendering")

const TemplateTraining = () => {
  const [currentView, setCurrentView] = useState(VIEW_STATES.SETTINGS)
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
    tools: {
      desktopControl: true,
      commandLine: false,
      fileEditor: true,
    },
    configuration: {
      sapSetup: true,
    },
    targetApp: "SAP2000",
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
        tools: {
          desktopControl: true,
          commandLine: false,
          fileEditor: true,
        },
        configuration: {
          sapSetup: true,
        },
        targetApp: "SAP2000",
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
                  tools: agent.tools,
                  targetApp: agent.targetApp,
                }
                console.log("🚀 Sending agent data via IPC:", agentDataToSend)
                console.log("🚀 Agent tools being sent:", agentDataToSend.tools)
                console.log(
                  "🚀 Agent targetApp being sent:",
                  agentDataToSend.targetApp
                )

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
                    tools: agentNameOrData.tools || {},
                    configuration: agentNameOrData.configuration || {
                      sapSetup: false,
                    },
                    targetApp: agentNameOrData.targetApp || "",
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
                  tools: {},
                  configuration: { sapSetup: false },
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
                tools: agentInfo.tools,
                configuration: agentInfo.configuration,
              }

              setAgentData(updatedAgentData)

              // Send updated agent data to main window via IPC
              if (window.electron?.ipcRenderer?.invoke) {
                const agentDataToSend = {
                  agentId: updatedAgentData.agentId,
                  name: updatedAgentData.name,
                  description: updatedAgentData.description,
                  tools: updatedAgentData.tools,
                  configuration: updatedAgentData.configuration,
                  targetApp:
                    updatedAgentData.targetApp ||
                    (updatedAgentData.name === "Structural-Engineer"
                      ? "SAP2000"
                      : ""),
                }
                console.log(
                  "🚀 Sending updated agent data via IPC:",
                  agentDataToSend
                )
                console.log(
                  "🚀 Updated agent tools being sent:",
                  agentDataToSend.tools
                )
                console.log(
                  "🚀 Agent data JSON string:",
                  JSON.stringify(agentDataToSend)
                )
                console.log("🚀 Agent data keys:", Object.keys(agentDataToSend))
                console.log(
                  "🚀 Agent data values:",
                  Object.values(agentDataToSend)
                )

                // Ensure all required fields are present
                if (!agentDataToSend.agentId || !agentDataToSend.name) {
                  console.error(
                    "🚀 Missing required fields in agent data:",
                    agentDataToSend
                  )
                }

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
                AgentHubService.updateAgent(agentData.agentId, agentInfo)
              } else {
                // Creating new agent
                AgentHubService.createAgent(agentInfo)
              }

              setCurrentView(VIEW_STATES.AGENT_HUB)
            }}
            onTrainUI={(agentInfo) => {
              const updatedAgentData = {
                ...agentData,
                name: agentInfo.name,
                description: agentInfo.description,
                prompt: agentInfo.prompt,
                tools: agentInfo.tools,
                configuration: agentInfo.configuration,
              }

              setAgentData(updatedAgentData)

              // Send updated agent data to main window via IPC
              if (window.electron?.ipcRenderer?.invoke) {
                const agentDataToSend = {
                  agentId: updatedAgentData.agentId,
                  name: updatedAgentData.name,
                  description: updatedAgentData.description,
                  tools: updatedAgentData.tools,
                  configuration: updatedAgentData.configuration,
                  targetApp:
                    updatedAgentData.targetApp ||
                    (updatedAgentData.name === "Structural-Engineer"
                      ? "SAP2000"
                      : ""),
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
              setCurrentScreenshot(null)
              setCurrentView(VIEW_STATES.PAGE_EDITOR)
            }}
            onEditPage={(screenshot) => {
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

  return (
    <div className="template-training">
      {currentView !== VIEW_STATES.SETTINGS && (
        <TemplateNavigation
          currentView={currentView}
          agentName={agentData.name}
          pageName={pageName}
          onNavigate={handleNavigate}
          pageTitle={getPageTitle()}
          currentScreenshot={currentScreenshot}
        />
      )}
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
