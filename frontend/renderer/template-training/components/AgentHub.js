import {
  faBoxArchive,
  faFileImport,
  faPen,
  faPlus,
  faTrash,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect } from "react"
import { ActionTypes } from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import AgentHubService from "../services/agentHubService"
import "../styles/components/AgentHub.scss"

const AgentHub = ({ onSelectAgent, selectedAgentId, onAgentSelect }) => {
  const { state, dispatch } = useAppState()
  const { agents, loading, error } = state.agentHub

  useEffect(() => {
    // Only fetch if we don't have agents cached
    if (agents.length === 0 && !loading && !error) {
      dispatch({ type: ActionTypes.SET_AGENT_HUB_LOADING, payload: true })
      AgentHubService.listAgents()
    }
  }, [agents.length, loading, error, dispatch])

  const handleCreate = () => {
    // Navigate to agent setup for creating new agent
    onSelectAgent(null) // Pass null to indicate new agent creation
  }

  const handleImport = () => {
    // Create file input element
    const input = document.createElement("input")
    input.type = "file"
    input.accept = ".agent,application/json"
    input.style.display = "none"

    input.onchange = (event) => {
      const file = event.target.files[0]
      if (!file) return

      // Read the file
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const agentData = JSON.parse(e.target.result)

          // Validate basic structure
          if (!agentData.name) {
            alert("Invalid agent file: missing name field")
            return
          }

          // Create new agent with imported data
          const importedAgent = {
            name: agentData.name,
            description: agentData.description || "",
            prompt: agentData.prompt || "",
            tools: agentData.tools || {},
            targetApp: agentData.targetApp || "",
          }

          // Call the backend to create the agent
          AgentHubService.createAgent(importedAgent)
        } catch (error) {
          alert("Failed to parse agent file. Please check the file format.")
          console.error("Import error:", error)
        }
      }

      reader.readAsText(file)
      document.body.removeChild(input)
    }

    document.body.appendChild(input)
    input.click()
  }

  const handleExport = (agent) => {
    // Create complete agent file content with all available fields
    const agentData = {
      schemaVersion: "1.0.0",
      agentId: agent.agentId,
      name: agent.name,
      description: agent.description || "",
      prompt: agent.prompt || "",
      tools: agent.tools || {},
      targetApp: agent.targetApp || "",
      createdAt: agent.last_modified || new Date().toISOString(),
      updatedAt: agent.last_modified || new Date().toISOString(),
      pagesCount: agent.pagesCount || 0,
      templatesCount: agent.templatesCount || 0,
      pages: [],
      templates: [],
    }

    // Convert to JSON and create download
    const jsonContent = JSON.stringify(agentData, null, 2)
    const blob = new Blob([jsonContent], { type: "application/json" })
    const url = URL.createObjectURL(blob)

    // Create download link
    const link = document.createElement("a")
    link.href = url
    link.download = `${agent.name || "agent"}.agent`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleDelete = (agent) => {
    if (confirm(`Delete agent "${agent.name}"?`))
      AgentHubService.deleteAgent(agent.agentId)
  }

  if (loading) {
    return (
      <div className="agent-hub">
        <div style={{ padding: "2rem", textAlign: "center", color: "#9C9B9F" }}>
          Loading agents...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="agent-hub">
        <div style={{ padding: "2rem", textAlign: "center", color: "#f0b7b7" }}>
          Error: {error}
        </div>
      </div>
    )
  }

  return (
    <div className="agent-hub">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px",
        }}
      >
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={handleImport} className="btn-secondary">
            <FontAwesomeIcon icon={faFileImport} /> Import
          </button>
          <button onClick={handleCreate} className="btn-primary">
            <FontAwesomeIcon icon={faPlus} /> New Agent
          </button>
        </div>
      </div>

      <div className="agent-table">
        <div className="agent-table-header">
          <div className="col name">Name</div>
          <div className="col app">Target App</div>
          <div className="col updated">Updated</div>
          <div className="col actions">Actions</div>
        </div>
        <div className="agent-table-body">
          {agents.length === 0 ? (
            <div
              style={{
                padding: "2rem",
                textAlign: "center",
                color: "#9C9B9F",
              }}
            >
              No agents found
            </div>
          ) : (
            agents.map((agent) => (
              <div
                className={`agent-row ${
                  selectedAgentId === agent.agentId ? "selected" : ""
                }`}
                key={agent.agentId || agent.name}
                onClick={() => {
                  console.log(
                    "🎯 Agent row clicked:",
                    agent.name,
                    "ID:",
                    agent.agentId
                  )
                  console.log("🎯 onAgentSelect function:", onAgentSelect)
                  console.log("🎯 onAgentSelect type:", typeof onAgentSelect)
                  console.log("🎯 onAgentSelect exists:", !!onAgentSelect)
                  console.log("🎯 Full agent data:", agent)

                  try {
                    if (onAgentSelect) {
                      console.log(
                        "🎯 About to call onAgentSelect with agent:",
                        agent
                      )
                      onAgentSelect(agent)
                      console.log("🎯 Successfully called onAgentSelect")
                    } else {
                      console.warn("⚠️ onAgentSelect callback not provided")
                      console.log("⚠️ Available props:", {
                        onSelectAgent,
                        selectedAgentId,
                        onAgentSelect,
                      })
                    }
                  } catch (error) {
                    console.error("🎯 Error calling onAgentSelect:", error)
                  }
                }}
              >
                <div className="col name">{agent.name || "Unnamed Agent"}</div>
                <div className="col app">{agent.targetApp || "-"}</div>
                <div className="col updated">
                  {agent.last_modified
                    ? new Date(agent.last_modified).toLocaleDateString()
                    : "-"}
                </div>
                <div className="col actions">
                  <button
                    className="icon-btn"
                    onClick={(e) => {
                      e.stopPropagation() // Prevent row selection when clicking edit
                      onSelectAgent(agent)
                    }}
                    title="Edit"
                  >
                    <FontAwesomeIcon icon={faPen} />
                  </button>
                  <button
                    className="icon-btn"
                    onClick={(e) => {
                      e.stopPropagation() // Prevent row selection when clicking export
                      handleExport(agent)
                    }}
                    title="Export"
                  >
                    <FontAwesomeIcon icon={faBoxArchive} />
                  </button>
                  <button
                    className="icon-btn danger"
                    onClick={(e) => {
                      e.stopPropagation() // Prevent row selection when clicking delete
                      handleDelete(agent)
                    }}
                    title="Delete"
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default AgentHub
