const MESSAGE_TYPES = {
  USER: "user",
  AI_RESPONSE: "ai_response",
  AI_RESPONSE_STREAM: "ai_response_stream",
  TOOL_RESULT: "tool_result",
  TOOL_USE_GROUP: "tool_use_group",
}

// States
const AgentStatus = {
  STOPPED: "STOPPED",
  RUNNING: "RUNNING",
  STOPPING: "STOPPING",
}

const AgentMode = Object.freeze({
  MANUAL: "MANUAL",
  SEMI_AUTO: "SEMI_AUTO",
  AUTO: "AUTO",
})

// SAP Connection status constants
const SAPConnectionStatus = Object.freeze({
  DISCONNECTED: "DISCONNECTED",
  CONNECTING: "CONNECTING",
  CONNECTED: "CONNECTED",
  UNKNOWN: "UNKNOWN",
})

// Desktop Connection status constants
const DesktopConnectionStatus = Object.freeze({
  DISCONNECTED: "DISCONNECTED",
  CONNECTING: "CONNECTING",
  CONNECTED: "CONNECTED",
  UNKNOWN: "UNKNOWN",
})

const ButtonsBarHeight = 38

// Action types
const ActionTypes = {
  SET_CONNECTION_STATUS: "SET_CONNECTION_STATUS",
  SET_AGENT_STATE: "SET_AGENT_STATE",
  SET_CHAT_INPUT: "SET_CHAT_INPUT",
  ADD_CHAT_MESSAGE: "ADD_CHAT_MESSAGE",
  SET_ERROR: "SET_ERROR",
  START_PROCESSING: "START_PROCESSING",
  STOP_PROCESSING: "STOP_PROCESSING",
  UPDATE_PENDING_TOOLS: "UPDATE_PENDING_TOOLS",
  SET_COMPASS_WINDOW_STATE: "SET_COMPASS_WINDOW_STATE",
  SET_SCALING_FACTORS: "SET_SCALING_FACTORS",
  SET_WORKFLOWS: "SET_WORKFLOWS",
  SET_SAP_CONNECTION_STATUS: "SET_SAP_CONNECTION_STATUS",
  SET_DESKTOP_CONNECTION_STATUS: "SET_DESKTOP_CONNECTION_STATUS",
  RESET_CHAT: "RESET_CHAT",
}

const WorkspaceWindowsConf = {
  MIN_EDITOR_WIN_WIDTH: 300,
  MAX_EDITOR_WIN_WIDTH: 800,
  MIN_TERMINAL_WIN_HEIGHT: 200,
}

module.exports = {
  MESSAGE_TYPES,
  AgentStatus,
  ButtonsBarHeight,
  ActionTypes,
  AgentMode,
  WorkspaceWindowsConf,
  SAPConnectionStatus,
  DesktopConnectionStatus,
}
