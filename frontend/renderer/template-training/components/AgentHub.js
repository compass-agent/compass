import {
  faBoxArchive,
  faCheck,
  faEllipsisVertical,
  faFileImport,
  faPen,
  faPlus,
  faTrash,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useRef, useState } from "react"
import { ActionTypes } from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import AgentHubService from "../services/agentHubService"
import "../styles/components/AgentHub.scss"

const AgentHub = ({ onSelectAgent, selectedAgentId, onAgentSelect }) => {
  const { state, dispatch } = useAppState()
  const { agents, loading, error } = state.agentHub
  const { connected } = state.connection
  const hasAttemptedFetch = useRef(false)
  const [openDropdown, setOpenDropdown] = useState(null)

  // Reset fetch attempt when WebSocket connects
  useEffect(() => {
    if (connected) {
      hasAttemptedFetch.current = false
    }
  }, [connected])

  useEffect(() => {
    // Only fetch if we don't have agents cached, haven't attempted to fetch yet, and WebSocket is connected
    if (
      agents.length === 0 &&
      !loading &&
      !error &&
      !hasAttemptedFetch.current &&
      connected
    ) {
      hasAttemptedFetch.current = true
      dispatch({ type: ActionTypes.SET_AGENT_HUB_LOADING, payload: true })
      AgentHubService.listAgents()
    }
  }, [agents.length, loading, error, connected])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setOpenDropdown(null)
    if (openDropdown) {
      document.addEventListener("click", handleClickOutside)
      return () => document.removeEventListener("click", handleClickOutside)
    }
  }, [openDropdown])

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
          // Send the complete file content to backend for processing
          const fileContent = e.target.result

          // Basic JSON validation
          JSON.parse(fileContent) // This will throw if invalid JSON

          // Send to backend for complete import (agent + pages + templates)
          AgentHubService.importAgent(fileContent)
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
    // Use backend export to get complete data (agent + pages + templates)
    AgentHubService.exportAgent(agent.agentId)
  }

  const handleDelete = (agent) => {
    const confirmMessage = `Delete agent "${
      agent.name
    }"?\n\nThis will permanently delete:\n• The agent configuration\n• All training pages (${
      agent.pagesCount || 0
    })\n• All UI templates (${
      agent.templatesCount || 0
    })\n\nThis action cannot be undone.`

    if (confirm(confirmMessage)) {
      AgentHubService.deleteAgent(agent.agentId)
    }
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
          <div className="col menu"></div>
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
                <div className="col menu">
                  <div className="dropdown-container">
                    <button
                      className="menu-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        setOpenDropdown(
                          openDropdown === agent.agentId ? null : agent.agentId
                        )
                      }}
                      title="More actions"
                    >
                      <FontAwesomeIcon icon={faEllipsisVertical} />
                    </button>
                    {openDropdown === agent.agentId && (
                      <div className="dropdown-menu">
                        <button
                          className={`dropdown-item ${
                            selectedAgentId === agent.agentId ? "selected" : ""
                          }`}
                          onClick={(e) => {
                            e.stopPropagation()
                            setOpenDropdown(null)
                            if (onAgentSelect) {
                              onAgentSelect(agent)
                            }
                          }}
                        >
                          <FontAwesomeIcon icon={faCheck} />
                          {selectedAgentId === agent.agentId
                            ? "Selected"
                            : "Select"}
                        </button>
                        <div className="dropdown-divider"></div>
                        <button
                          className="dropdown-item"
                          onClick={(e) => {
                            e.stopPropagation()
                            setOpenDropdown(null)
                            onSelectAgent(agent)
                          }}
                        >
                          <FontAwesomeIcon icon={faPen} />
                          Edit
                        </button>
                        <button
                          className="dropdown-item"
                          onClick={(e) => {
                            e.stopPropagation()
                            setOpenDropdown(null)
                            handleExport(agent)
                          }}
                        >
                          <FontAwesomeIcon icon={faBoxArchive} />
                          Export
                        </button>
                        <button
                          className="dropdown-item danger"
                          onClick={(e) => {
                            e.stopPropagation()
                            setOpenDropdown(null)
                            handleDelete(agent)
                          }}
                        >
                          <FontAwesomeIcon icon={faTrash} />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
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
