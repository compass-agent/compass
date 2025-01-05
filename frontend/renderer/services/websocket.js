import io from "socket.io-client";

class WebSocketService {
  constructor() {
    this.socket = null;
    this.stateHandlers = null;
  }

  setStateHandlers(handlers) {
    this.stateHandlers = handlers;
  }

  connect() {
    if (this.socket) {
      this.socket.disconnect();
    }

    this.socket = io("http://localhost:5001", {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ["websocket"],
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      this.stateHandlers?.onConnect();
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
      this.stateHandlers?.onDisconnect();
    });

    this.socket.on("state_update", (data) => {
      console.log("WebSocket received state update:", data);
      this.stateHandlers?.onStateUpdate(data);
    });

    this.socket.on("response", (data) => {
      console.log("WebSocket received response:", data);
      this.stateHandlers?.onResponse(data);
    });

    this.socket.on("minimize-window", (data) => {
      console.log("WebSocket received Windows minimize action:", data);
      this.stateHandlers?.onCompassWindowState(data);
    });

    this.socket.on("restore-window", (data) => {
      console.log("WebSocket received Windows restore action:", data);
      this.stateHandlers?.onCompassWindowState(data);
    });

    this.socket.on("error", (error) => {
      console.error("WebSocket error:", error);
      this.stateHandlers?.onError(error);
    });

    this.socket.on("connect_error", () => {
      console.log("WebSocket connection failed");
      this.stateHandlers?.onError({
        message: "Connection failed. Retrying...",
      });
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
      this.socket.emit("message", { text: message });
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
}

export default new WebSocketService();
