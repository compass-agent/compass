import WebSocketService from "../../common/services/websocket"

const AgentHubService = {
  listAgents() {
    WebSocketService.agentHub("list")
  },
  createAgent(agentData) {
    WebSocketService.agentHub("create", agentData)
  },
  updateAgent(agentId, agentData) {
    WebSocketService.agentHub("update", { agentId, ...agentData })
  },
  importAgent(fileName) {
    WebSocketService.agentHub("import", { fileName })
  },
  exportAgent(agentId) {
    WebSocketService.agentHub("export", { agentId })
  },
  renameAgent(agentId, name) {
    WebSocketService.agentHub("rename", { agentId, name })
  },
  deleteAgent(agentId) {
    WebSocketService.agentHub("delete", { agentId })
  },
  getAgent(agentId) {
    WebSocketService.agentHub("get", { agentId })
  },
  addHandler(handler) {
    WebSocketService.addHandler("onAgentHub", handler)
  },
  removeHandler(handler) {
    WebSocketService.removeHandler("onAgentHub", handler)
  },
}

export default AgentHubService
