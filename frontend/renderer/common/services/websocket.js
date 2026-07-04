import io from "socket.io-client"

class WebSocketService {
  constructor() {
    this.socket = null
    this.stateHandlers = {
      onConnect: new Set(),
      onDisconnect: new Set(),
      onError: new Set(),
      onWorkflowsList: new Set(),
      onResponse: new Set(),
      onStateUpdate: new Set(),
      onCompassWindowState: new Set(),
      onScalingFactors: new Set(),
      onChatReset: new Set(),
      onAgentsList: new Set(),
      onScreenshotsList: new Set(),
      onDetectionResult: null,
      onTemplateSaved: null,
      onTemplatesSaved: null,
      onSAPConnectionStatus: new Set(),
      onDesktopConnectionStatus: new Set(),
      onAgentHub: new Set(),
      onDeletePageResult: new Set(),
      onBackendStatus: new Set(),
      onApiKeyValidation: new Set(),
    }
    this.reconnectAttempts = 0
    this.heartbeatInterval = null
    // Generous ceiling: in production the packaged backend can take a while
    // to boot on first run (database seeding), and we must outlast it.
    this.maxReconnectAttempts = 60
  }

  addHandler(event, handler) {
    const current = this.stateHandlers[event]
    if (current instanceof Set) {
      current.add(handler)
    } else if (Object.prototype.hasOwnProperty.call(this.stateHandlers, event)) {
      this.stateHandlers[event] = handler
    }
  }

  removeHandler(event, handler) {
    const current = this.stateHandlers[event]
    if (current instanceof Set) {
      current.delete(handler)
    } else if (current === handler) {
      this.stateHandlers[event] = null
    }
  }

  emitToHandlers(event, data) {
    const handlers = this.stateHandlers[event]
    if (handlers instanceof Set) {
      handlers.forEach((handler) => handler(data))
    } else if (typeof handlers === "function") {
      handlers(data)
    }
  }

  connect() {
    console.log("WebSocketService: connecting to Compass backend")
    if (this.socket) {
      this.socket.disconnect()
    }
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }

    this.socket = io("http://127.0.0.1:5001", {
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 5000,
      transports: ["polling", "websocket"],
      forceNew: true,
    })

    this.socket.on("connect", () => {
      console.log(
        `WebSocketService: connected via ${this.socket.io.engine.transport.name}`
      )
      this.reconnectAttempts = 0
      this.emitToHandlers("onConnect")
    })

    this.socket.on("disconnect", (reason) => {
      console.log(`WebSocketService: disconnected (${reason})`)
      this.emitToHandlers("onDisconnect", reason)

      if (reason === "io server disconnect") {
        // Server initiated disconnect, try reconnecting
        this.socket.connect()
      }
    })

    this.socket.on("connect_error", (error) => {
      this.reconnectAttempts++
      console.log(
        `WebSocketService: connect_error ${this.reconnectAttempts}/${this.maxReconnectAttempts}: ${error.message}`
      )

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this.socket.disconnect()
      }

      this.emitToHandlers("onError", {
        message: `Connection failed (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}). ${error.message}`,
      })
    })

    // Add heartbeat to check connection
    this.heartbeatInterval = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit("ping")
      }
    }, 25000)

    this.socket.on("pong", () => {})

    this.socket.on("state_update", (data) => {
      this.emitToHandlers("onStateUpdate", data)
    })

    this.socket.on("response", (data) => {
      this.emitToHandlers("onResponse", data)
    })

    this.socket.on("minimize-window", (data) => {
      this.emitToHandlers("onCompassWindowState", data)
    })

    this.socket.on("restore-window", (data) => {
      this.emitToHandlers("onCompassWindowState", data)
    })

    this.socket.on("error", (error) => {
      console.error("WebSocket error:", error)
      this.emitToHandlers("onError", error)
    })

    this.socket.on("detection_result", (data) => {
      this.emitToHandlers("onDetectionResult", data)
    })

    this.socket.on("template_saved", (data) => {
      this.emitToHandlers("onTemplateSaved", data)
    })

    this.socket.on("scaling_factors", (data) => {
      this.emitToHandlers("onScalingFactors", data)
    })

    this.socket.on("chat_reset", () => {
      this.emitToHandlers("onChatReset")
    })

    this.socket.on("screenshots_list", (data) => {
      this.emitToHandlers("onScreenshotsList", data)
    })

    this.socket.on("workflows_list", (data) => {
      this.emitToHandlers("onWorkflowsList", data)
    })

    this.socket.on("agents_list", (data) => {
      this.emitToHandlers("onAgentsList", data)
    })

    this.socket.on("agent_hub_result", (data) => {
      this.emitToHandlers("onAgentHub", data)
    })

    this.socket.on("delete_page_result", (data) => {
      this.emitToHandlers("onDeletePageResult", data)
    })

    this.socket.on("templates_saved", (data) => {
      this.emitToHandlers("onTemplatesSaved", data)
    })

    // Add SAP connection status event handler
    this.socket.on("sap_connection_status", (data) => {
      this.emitToHandlers("onSAPConnectionStatus", data)
    })

    this.socket.on("sap_config_status", (data) => {
      // We can use the same handler for config status updates
      this.emitToHandlers("onSAPConnectionStatus", {
        configStatus: data,
      })
    })

    // Add Desktop connection status event handler
    this.socket.on("desktop_connection_status", (data) => {
      this.emitToHandlers("onDesktopConnectionStatus", data)
    })

    // Backend readiness (LLM configured or not)
    this.socket.on("backend_status", (data) => {
      this.emitToHandlers("onBackendStatus", data)
    })

    // API key validation result (used by the settings/onboarding UI)
    this.socket.on("api_key_validation", (data) => {
      this.emitToHandlers("onApiKeyValidation", data)
    })
  }

  disconnect() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  sendMessage(message) {
    if (this.socket?.connected) {
      if (typeof message === "string") {
        // Handle legacy string messages
        this.socket.emit("message", { text: message })
      } else {
        // Handle new message format with optional image and workflow
        this.socket.emit("message", {
          text: message.text,
          image_data: message.image_data,
          workflow_name: message.workflow_name,
        })
      }
    }
  }

  updateControlState(state) {
    if (this.socket?.connected) {
      this.socket.emit("control_update", state)
    }
  }

  executeToolAndGenerateAction() {
    if (this.socket?.connected) {
      this.socket.emit("execute_tool_and_generate_action")
    }
  }

  uploadScreenshot(imageData, agentName) {
    if (this.socket?.connected) {
      this.socket.emit("upload_screenshot", {
        image: imageData,
        agent_name: agentName,
      })
    }
  }

  getScreenshots(agentName) {
    if (this.socket?.connected) {
      this.socket.emit("get_screenshots", {
        agent_name: agentName,
      })
    }
  }

  setStateHandlers(handlers) {
    Object.entries(handlers).forEach(([event, handler]) => {
      if (handler) {
        this.addHandler(event, handler)
      }
    })
  }

  getWorkflows() {
    if (this.socket?.connected) {
      this.socket.emit("get_workflows")
    }
  }

  handleNewChat(agentName) {
    if (this.socket?.connected) {
      this.socket.emit("new_chat", { agent_name: agentName })
    }
  }

  getAgents() {
    if (this.socket?.connected) {
      this.socket.emit("get_agents")
    }
  }

  saveTemplates(data) {
    if (this.socket?.connected) {
      this.socket.emit("save_templates", data)
    }
  }

  // New methods for SAP connection
  connectToSAP() {
    if (this.socket?.connected) {
      this.socket.emit("connect_to_sap")
    }
  }

  loadSAPConfig(configPath) {
    if (this.socket?.connected) {
      this.socket.emit("load_sap_config", { config_path: configPath })
    }
  }

  getSAPConnectionStatus() {
    if (this.socket?.connected) {
      this.socket.emit("get_sap_connection_status")
    }
  }
  // New methods for Desktop connection
  connectToDesktop() {
    if (this.socket?.connected) {
      this.socket.emit("connect_to_desktop")
    }
  }

  getDesktopConnectionStatus() {
    if (this.socket?.connected) {
      this.socket.emit("get_desktop_connection_status")
    }
  }

  // Backend readiness / API key management
  getBackendStatus() {
    if (this.socket?.connected) {
      this.socket.emit("get_backend_status")
    }
  }

  validateApiKey(provider, apiKey) {
    if (this.socket?.connected) {
      this.socket.emit("validate_api_key", { provider, api_key: apiKey })
    }
  }

  initializeAgent() {
    if (this.socket?.connected) {
      this.socket.emit("initialize_agent")
    }
  }

  // General Agent Hub action sender
  agentHub(action, payload = {}) {
    if (this.socket?.connected) {
      this.socket.emit("agent_hub", { action, ...payload })
    }
  }

  // Page management
  deletePage(pageId) {
    if (this.socket?.connected) {
      this.socket.emit("delete_page", { pageId })
    }
  }
}

// Create a singleton instance
const instance = new WebSocketService()
export default instance
