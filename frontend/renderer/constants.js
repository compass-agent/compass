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

module.exports = { MESSAGE_TYPES, AgentStatus, ButtonsBarHeight };
