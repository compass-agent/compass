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
  importAgent(importData) {
    WebSocketService.agentHub("import", { importData })
  },
  exportAgent(agentId) {
    WebSocketService.agentHub("export", { agentId })
  },
  deleteAgent(agentId) {
    WebSocketService.agentHub("delete", { agentId })
  },
}

export default AgentHubService
