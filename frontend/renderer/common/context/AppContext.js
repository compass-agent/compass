import React, { createContext, useContext, useEffect, useReducer } from "react"
import {
  ActionTypes,
  AgentMode,
  AgentStatus,
  DesktopConnectionStatus,
  SAPConnectionStatus,
} from "../constants"
import WebSocketService from "../services/websocket"

const AppContext = createContext()

// Initial state
const initialState = {
  connection: {
    connected: false,
    reconnecting: false,
    error: null,
  },
  agent: {
    mode: AgentMode.MANUAL,
    status: AgentStatus.STOPPED,
    currentTask: null,
    pendingTools: 0,
  },
  chat: {
    messages: [],
    error: null,
    currentInput: "",
  },

  compassWindow: {
    actionType: null,
  },

  scaling: {
    xFactor: 1.147,
    yFactor: 1.194,
  },

  workflows: [],

  sap: {
    connectionStatus: SAPConnectionStatus.DISCONNECTED,
    message: null,
    configStatus: { success: false, message: null },
  },

  desktop: {
    connectionStatus: DesktopConnectionStatus.DISCONNECTED,
    message: null,
  },

  agentHub: {
    agents: [],
    loading: false,
    selectedAgent: null,
    error: null,
    successMessage: null,
  },
}

// Reducer
function appReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_CONNECTION_STATUS:
      return {
        ...state,
        connection: { ...state.connection, ...action.payload },
      }

    case ActionTypes.SET_AGENT_STATE:
      return {
        ...state,
        agent: {
          ...state.agent,
          ...action.payload,
          pendingTools: action.payload.pendingTools ?? state.agent.pendingTools,
        },
      }

    case ActionTypes.SET_CHAT_INPUT:
      return {
        ...state,
        chat: { ...state.chat, currentInput: action.payload },
      }

    case ActionTypes.ADD_CHAT_MESSAGE:
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: [
            ...state.chat.messages,
            {
              ...action.payload,
              timestamp: action.payload.timestamp || new Date().toISOString(),
            },
          ],
        },
      }

    case ActionTypes.SET_ERROR:
      return {
        ...state,
        chat: { ...state.chat, error: action.payload },
        connection: { ...state.connection, error: action.payload },
      }

    case ActionTypes.START_PROCESSING:
      return {
        ...state,
        agent: {
          ...state.agent,
          status: AgentStatus.RUNNING,
        },
      }

    case ActionTypes.STOP_PROCESSING:
      return {
        ...state,
        agent: {
          ...state.agent,
          status: AgentStatus.STOPPING,
        },
      }

    case ActionTypes.UPDATE_PENDING_TOOLS:
      return {
        ...state,
        agent: {
          ...state.agent,
          pendingTools: action.payload,
        },
      }

    case ActionTypes.SET_COMPASS_WINDOW_STATE:
      return {
        ...state,
        compassWindow: {
          actionType: action.payload,
        },
      }

    case ActionTypes.SET_SCALING_FACTORS:
      return {
        ...state,
        scaling: {
          xFactor: action.payload.x_factor,
          yFactor: action.payload.y_factor,
        },
      }

    case ActionTypes.RESET_CHAT:
      return {
        ...state,
        chat: {
          messages: [],
          error: null,
          currentInput: "",
        },
        agent: {
          ...state.agent,
          status: AgentStatus.STOPPED,
          currentTask: null,
          pendingTools: 0,
        },
      }

    case ActionTypes.SET_WORKFLOWS:
      return {
        ...state,
        workflows: action.payload,
      }

    case ActionTypes.SET_SAP_CONNECTION_STATUS:
      return {
        ...state,
        sap: {
          ...state.sap,
          connectionStatus: action.payload.status || state.sap.connectionStatus,
          message: Object.prototype.hasOwnProperty.call(action.payload, "message")
            ? action.payload.message
            : state.sap.message,
          configStatus: Object.prototype.hasOwnProperty.call(action.payload, "configStatus")
            ? action.payload.configStatus
            : state.sap.configStatus,
        },
      }

    case ActionTypes.SET_DESKTOP_CONNECTION_STATUS:
      return {
        ...state,
        desktop: {
          ...state.desktop,
          connectionStatus:
            action.payload.status || state.desktop.connectionStatus,
          message: action.payload.message || state.desktop.message,
        },
      }

    // Agent Hub management cases
    case ActionTypes.SET_AGENT_HUB_AGENTS:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          agents: action.payload,
          loading: false,
          error: null,
        },
      }

    case ActionTypes.SET_AGENT_HUB_LOADING:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          loading: action.payload,
        },
      }

    case ActionTypes.AGENT_HUB_ADD_AGENT:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          agents: [...state.agentHub.agents, action.payload],
        },
      }

    case ActionTypes.AGENT_HUB_UPDATE_AGENT:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          agents: state.agentHub.agents.map((agent) =>
            agent.agentId === action.payload.agentId
              ? { ...agent, ...action.payload }
              : agent
          ),
        },
      }

    case ActionTypes.AGENT_HUB_REMOVE_AGENT:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          agents: state.agentHub.agents.filter(
            (agent) => agent.agentId !== action.payload
          ),
        },
      }

    case ActionTypes.SET_AGENT_HUB_ERROR:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          error: action.payload,
          loading: false,
        },
      }

    case ActionTypes.SHOW_AGENT_HUB_SUCCESS:
      return {
        ...state,
        agentHub: {
          ...state.agentHub,
          successMessage: action.payload,
        },
      }

    default:
      return state
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

  // Setup WebSocket handlers
  useEffect(() => {
    WebSocketService.setStateHandlers({
      onConnect: () => {
        // When connection is established, update connection status and fetch workflows
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: true, error: null },
        })
      },

      onDisconnect: () =>
        dispatch({
          type: ActionTypes.SET_CONNECTION_STATUS,
          payload: { connected: false },
        }),

      onResponse: (data) => {
        dispatch({
          type: ActionTypes.ADD_CHAT_MESSAGE,
          payload: {
            ...data,
            timestamp: new Date().toISOString(),
          },
        })
      },

      onStateUpdate: (data) => {
        dispatch({
          type: ActionTypes.SET_AGENT_STATE,
          payload: data,
        })
      },

      onCompassWindowState: (actionString) => {
        dispatch({
          type: ActionTypes.SET_COMPASS_WINDOW_STATE,
          payload: actionString,
        })
      },

      onError: (error) =>
        dispatch({
          type: ActionTypes.SET_ERROR,
          payload: error.message,
        }),

      onScalingFactors: (data) => {
        dispatch({
          type: ActionTypes.SET_SCALING_FACTORS,
          payload: data,
        })
      },

      onChatReset: () => {
        dispatch({
          type: ActionTypes.RESET_CHAT,
        })
      },

      onWorkflowsList: (data) => {
        dispatch({
          type: ActionTypes.SET_WORKFLOWS,
          payload: data.workflows,
        })
      },

      onSAPConnectionStatus: (data) => {
        dispatch({
          type: ActionTypes.SET_SAP_CONNECTION_STATUS,
          payload: data,
        })
      },

      onDesktopConnectionStatus: (data) => {
        dispatch({
          type: ActionTypes.SET_DESKTOP_CONNECTION_STATUS,
          payload: data,
        })
      },

      // Agent Hub handlers
      onAgentHub: (data) => {
        if (!data) return

        switch (data.action) {
          case "list":
            if (data.success && Array.isArray(data.agents)) {
              dispatch({
                type: ActionTypes.SET_AGENT_HUB_AGENTS,
                payload: data.agents,
              })
            }
            break
          case "create":
            if (data.success && data.agent) {
              dispatch({
                type: ActionTypes.AGENT_HUB_ADD_AGENT,
                payload: data.agent,
              })
            }
            break
          case "import":
            if (data.success && data.agent) {
              dispatch({
                type: ActionTypes.AGENT_HUB_ADD_AGENT,
                payload: data.agent,
              })
            } else if (!data.success && data.message) {
              alert(`Import failed: ${data.message}`)
            }
            break
          case "update":
            if (data.success && data.agent) {
              dispatch({
                type: ActionTypes.AGENT_HUB_UPDATE_AGENT,
                payload: data.agent,
              })
            }
            break

          case "delete":
            if (data.success && data.agentId) {
              // Show success dialog with deletion statistics
              if (data.message) {
                dispatch({
                  type: ActionTypes.SHOW_AGENT_HUB_SUCCESS,
                  payload: {
                    agentName: data.message.replace(
                      " and all training data deleted successfully",
                      ""
                    ),
                    pagesDeleted: data.pagesDeleted || 0,
                    templatesDeleted: data.templatesDeleted || 0,
                  },
                })
              }

              dispatch({
                type: ActionTypes.AGENT_HUB_REMOVE_AGENT,
                payload: data.agentId,
              })
            } else if (!data.success && data.message) {
              alert(`Failed to delete agent: ${data.message}`)
            }
            break
          case "export":
            if (data.success && data.content && data.filename) {
              // Decode base64 content and trigger download
              try {
                const jsonContent = atob(data.content)
                const blob = new Blob([jsonContent], {
                  type: "application/json",
                })
                const url = URL.createObjectURL(blob)

                // Create download link
                const link = document.createElement("a")
                link.href = url
                link.download = data.filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(url)
              } catch (error) {
                console.error("AGENT_HUB: Export download failed:", error)
              }
            } else if (!data.success && data.message) {
              console.error("AGENT_HUB: Export failed:", data.message)
            }
            break
          default:
            if (!data.success && data.message) {
              console.error("AGENT_HUB: Error:", data.message)
              dispatch({
                type: ActionTypes.SET_AGENT_HUB_ERROR,
                payload: data.message,
              })
            }
            break
        }
      },
    })

    WebSocketService.connect()

    // Request SAP and Desktop connection status on initial load
    setTimeout(() => {
      WebSocketService.getSAPConnectionStatus()
      WebSocketService.getDesktopConnectionStatus()
    }, 1000)

    return () => WebSocketService.disconnect()
  }, [])

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

// Custom hooks
export function useAppState() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error("useAppState must be used within an AppProvider")
  }
  return context
}
