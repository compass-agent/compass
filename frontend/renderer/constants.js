const MESSAGE_TYPES = {
  USER: "user",
  AI_RESPONSE: "ai_response",
  TOOL_USE: "tool_use",
  TOOL_RESULT: "tool_result",
};

// States
const AgentStatus = {
  IDLE: "IDLE",
  RUNNING: "RUNNING",
  STOPPING: "STOPPING",
};

const ButtonsBarHeight = 38;

// Action types
const ActionTypes = {
  SET_CONNECTION_STATUS: "SET_CONNECTION_STATUS",
  SET_AGENT_STATE: "",
  SET_CHAT_INPUT: "SET_CHAT_INPUT",
  ADD_CHAT_MESSAGE: "ADD_CHAT_MESSAGE",
  SET_ERROR: "SET_ERROR",
  START_PROCESSING: "START_PROCESSING",
  STOP_PROCESSING: "STOP_PROCESSING",
  UPDATE_PENDING_TOOLS: "UPDATE_PENDING_TOOLS",
  SET_COMPASS_WINDOW_STATE: "SET_COMPASS_WINDOW_STATE",
};

module.exports = { MESSAGE_TYPES, AgentStatus, ButtonsBarHeight, ActionTypes };
