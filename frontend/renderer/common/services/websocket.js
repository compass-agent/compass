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
      onTemplatesSaved: null,
      onSAPConnectionStatus: new Set(),
      onDesktopConnectionStatus: new Set(),
      onAgentHub: new Set(),
      onDeletePageResult: new Set(),
    }
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
  }

  addHandler(event, handler) {
    if (this.stateHandlers[event]) {
      this.stateHandlers[event].add(handler)
    }
  }

  removeHandler(event, handler) {
    if (this.stateHandlers[event]) {
      this.stateHandlers[event].delete(handler)
    }
  }

  connect() {
    if (this.socket) {
      this.socket.disconnect()
    }

    this.socket = io("http://localhost:5001", {
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 2000000,
      transports: ["websocket"],
      forceNew: true,
    })

    this.socket.on("connect", () => {
      this.reconnectAttempts = 0
      this.stateHandlers.onConnect.forEach((handler) => handler())
    })

    this.socket.on("disconnect", (reason) => {
      this.stateHandlers.onDisconnect.forEach((handler) => handler(reason))

      if (reason === "io server disconnect") {
        // Server initiated disconnect, try reconnecting
        this.socket.connect()
      }
    })

    this.socket.on("connect_error", (error) => {
      this.reconnectAttempts++

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this.socket.disconnect()
      }

      this.stateHandlers.onError.forEach((handler) =>
        handler({
          message: `Connection failed (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}). ${error.message}`,
        })
      )
    })

    // Add heartbeat to check connection
    setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit("ping")
      }
    }, 25000)

    this.socket.on("pong", () => {})

    this.socket.on("state_update", (data) => {
      this.stateHandlers.onStateUpdate.forEach((handler) => handler(data))
    })

    this.socket.on("response", (data) => {
      this.stateHandlers.onResponse.forEach((handler) => handler(data))
    })

    this.socket.on("minimize-window", (data) => {
      this.stateHandlers.onCompassWindowState.forEach((handler) =>
        handler(data)
      )
    })

    this.socket.on("restore-window", (data) => {
      this.stateHandlers.onCompassWindowState.forEach((handler) =>
        handler(data)
      )
    })

    this.socket.on("error", (error) => {
      console.error("WebSocket error:", error)
      this.stateHandlers.onError.forEach((handler) => handler(error))
    })

    this.socket.on("detection_result", (data) => {
      this.stateHandlers?.onDetectionResult?.(data)
    })

    this.socket.on("template_saved", (data) => {
      this.stateHandlers?.onTemplateSaved?.(data)
    })

    this.socket.on("scaling_factors", (data) => {
      this.stateHandlers.onScalingFactors.forEach((handler) => handler(data))
    })

    this.socket.on("chat_reset", () => {
      if (this.stateHandlers?.onChatReset)
        this.stateHandlers.onChatReset.forEach((handler) => handler())
    })

    this.socket.on("screenshots_list", (data) => {
      this.stateHandlers?.onScreenshotsList?.forEach((handler) => handler(data))
    })

    this.socket.on("workflows_list", (data) => {
      this.stateHandlers.onWorkflowsList.forEach((handler) => handler(data))
    })

    this.socket.on("agents_list", (data) => {
      this.stateHandlers?.onAgentsList?.forEach((handler) => handler(data))
    })

    this.socket.on("agent_hub_result", (data) => {
      this.stateHandlers.onAgentHub.forEach((handler) => handler(data))
    })

    this.socket.on("delete_page_result", (data) => {
      if (this.stateHandlers.onDeletePageResult) {
        this.stateHandlers.onDeletePageResult.forEach((handler) =>
          handler(data)
        )
      }
    })

    this.socket.on("templates_saved", (data) => {
      this.stateHandlers?.onTemplatesSaved?.(data)
    })

    // Add SAP connection status event handler
    this.socket.on("sap_connection_status", (data) => {
      this.stateHandlers.onSAPConnectionStatus.forEach((handler) =>
        handler(data)
      )
    })

    this.socket.on("sap_config_status", (data) => {
      // We can use the same handler for config status updates
      this.stateHandlers.onSAPConnectionStatus.forEach((handler) =>
        handler({
          configStatus: data,
        })
      )
    })

    // Add Desktop connection status event handler
    this.socket.on("desktop_connection_status", (data) => {
      this.stateHandlers.onDesktopConnectionStatus.forEach((handler) =>
        handler(data)
      )
    })
  }

  disconnect() {
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
