import io from "socket.io-client";

class WebSocketService {
  constructor() {
    this.socket = null;
    this.stateHandlers = {
      onConnect: new Set(),
      onDisconnect: new Set(),
      onError: new Set(),
      onWorkflowsList: new Set(),
      onResponse: new Set(),
      onStateUpdate: new Set(),
      onCompassWindowState: new Set(),
      onScalingFactors: new Set(),
      onChatReset: new Set()
    };
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
  }

  addHandler(event, handler) {
    if (this.stateHandlers[event]) {
      this.stateHandlers[event].add(handler);
    }
  }

  removeHandler(event, handler) {
    if (this.stateHandlers[event]) {
      this.stateHandlers[event].delete(handler);
    }
  }

  connect() {
    if (this.socket) {
      this.socket.disconnect();
    }

    this.socket = io("http://localhost:5001", {
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      transports: ["websocket"],
      forceNew: true
    });

    this.socket.on("connect", () => {
      console.log("📡 WebSocket connected with ID:", this.socket.id);
      this.reconnectAttempts = 0;
      this.stateHandlers.onConnect.forEach(handler => handler());
    });

    this.socket.on("disconnect", (reason) => {
      console.log("WebSocket disconnected. Reason:", reason);
      this.stateHandlers.onDisconnect.forEach(handler => handler(reason));
      
      if (reason === "io server disconnect") {
        // Server initiated disconnect, try reconnecting
        this.socket.connect();
      }
    });

    this.socket.on("connect_error", (error) => {
      this.reconnectAttempts++;
      console.log(`WebSocket connection failed (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}):`, error);
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log("Max reconnection attempts reached, stopping reconnection");
        this.socket.disconnect();
      }

      this.stateHandlers.onError.forEach(handler => handler({
        message: `Connection failed (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}). ${error.message}`,
      }));
    });

    // Add heartbeat to check connection
    setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping');
      }
    }, 25000);

    this.socket.on('pong', () => {
      console.log('Received pong from server');
    });

    this.socket.on("state_update", (data) => {
      console.log("WebSocket received state update:", data);
      this.stateHandlers.onStateUpdate.forEach(handler => handler(data));
    });

    this.socket.on("response", (data) => {
      console.log("WebSocket received response:", data);
      this.stateHandlers.onResponse.forEach(handler => handler(data));
    });

    this.socket.on("minimize-window", (data) => {
      console.log("WebSocket received Windows minimize action:", data);
      this.stateHandlers.onCompassWindowState.forEach(handler => handler(data));
    });

    this.socket.on("restore-window", (data) => {
      console.log("WebSocket received Windows restore action:", data);
      this.stateHandlers.onCompassWindowState.forEach(handler => handler(data));
    });

    this.socket.on("error", (error) => {
      console.error("WebSocket error:", error);
      this.stateHandlers.onError.forEach(handler => handler(error));
    });

    this.socket.on("detection_result", (data) => {
      console.log("WebSocket received detection result:", data);
      this.stateHandlers?.onDetectionResult?.(data);
    });

    this.socket.on("template_saved", (data) => {
      console.log("WebSocket template saved:", data);
      this.stateHandlers?.onTemplateSaved?.(data);
    });

    this.socket.on("scaling_factors", (data) => {
      console.log("WebSocket: Raw scaling factors data received:", data);
      console.log("WebSocket: x_factor =", data.x_factor, "y_factor =", data.y_factor);
      this.stateHandlers.onScalingFactors.forEach(handler => handler(data));
    });

    this.socket.on('chat_reset', () => {
      if (this.stateHandlers?.onChatReset) this.stateHandlers.onChatReset.forEach(handler => handler());
    });

    this.socket.on("screenshots_list", (data) => {
      console.log("WebSocket received screenshots list:", data);
      this.stateHandlers?.onScreenshotsList?.(data);
    });

    this.socket.on("workflows_list", (data) => {
      console.log("📦 WebSocket: Received workflows_list event:", data);
      this.stateHandlers.onWorkflowsList.forEach(handler => handler(data));
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  sendMessage(message) {
    if (this.socket?.connected) {
      if (typeof message === 'string') {
        // Handle legacy string messages
        this.socket.emit("message", { text: message });
      } else {
        // Handle new message format with optional image
        this.socket.emit("message", {
          text: message.text,
          image_data: message.image_data
        });
      }
    }
  }

  updateControlState(state) {
    if (this.socket?.connected) {
      this.socket.emit("control_update", state);
    }
  }

  executeNextTool() {
    if (this.socket?.connected) {
      console.log("WebSocket sending execute_next_tool");
      this.socket.emit("execute_next_tool");
    }
  }

  generateNextAction() {
    if (this.socket?.connected) {
      console.log("WebSocket sending generate_next_action");
      this.socket.emit("generate_next_action");
    }
  }

  executeToolAndGenerateAction() {
    if (this.socket?.connected) {
      console.log("WebSocket sending execute_tool_and_generate_action");
      this.socket.emit("execute_tool_and_generate_action");
    }
  }

  uploadScreenshot(imageData, agentName) {
    if (this.socket?.connected) {
      console.log("WebSocket sending upload_screenshot");
      this.socket.emit("upload_screenshot", {
        image: imageData,
        agent_name: agentName
      });
    }
  }

  saveTemplate(templateData) {
    if (this.socket?.connected) {
      console.log("WebSocket sending save_template with data:", templateData);
      this.socket.emit("save_template", templateData);
    } else {
      console.error("Socket not connected when trying to save template");
    }
  }

  getScreenshots(agentName) {
    if (this.socket?.connected) {
      console.log("WebSocket sending get_screenshots");
      this.socket.emit("get_screenshots", {
        agent_name: agentName
      });
    }
  }

  setStateHandlers(handlers) {
    Object.entries(handlers).forEach(([event, handler]) => {
      if (handler) {
        this.addHandler(event, handler);
      }
    });
  }

  getWorkflows() {
    if (this.socket?.connected) {
      console.log("🔍 WebSocket sending get_workflows request");
      this.socket.emit("get_workflows");
    } else {
      console.warn("Cannot get workflows - socket not connected");
    }
  }
}

export default new WebSocketService();
