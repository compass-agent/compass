import WebSocketService from './websocket';
import StateManager from './stateManager';

class MessageHandler {
  constructor() {
    this.messageQueue = [];
    this.isProcessing = false;
  }

  async handleIncomingMessage(message) {
    switch (message.type) {
      case 'ai':
        await this.handleAIResponse(message);
        break;
      case 'system':
        await this.handleSystemMessage(message);
        break;
      case 'error':
        await this.handleError(message);
        break;
      default:
        console.warn('Unknown message type:', message.type);
    }
  }

  async handleAIResponse(message) {
    const currentMessages = StateManager.getState('chat.messages');
    StateManager.setState('chat.messages', [...currentMessages, message]);
  }

  async handleSystemMessage(message) {
    switch (message.action) {
      case 'state_update':
        StateManager.setState('agent', message.data);
        break;
      case 'connection_update':
        StateManager.setState('connection', message.data);
        break;
      default:
        console.warn('Unknown system message:', message.action);
    }
  }

  async handleError(message) {
    StateManager.setState('chat.error', message.error);
    console.error('Error:', message.error);
  }

  async queueOutgoingMessage(message) {
    this.messageQueue.push(message);
    if (!this.isProcessing) {
      await this.processQueue();
    }
  }

  async processQueue() {
    if (this.messageQueue.length === 0) {
      this.isProcessing = false;
      return;
    }

    this.isProcessing = true;
    const message = this.messageQueue.shift();

    try {
      await WebSocketService.sendMessage(message);
    } catch (error) {
      console.error('Failed to send message:', error);
      StateManager.setState('chat.error', error.message);
    }

    await this.processQueue();
  }
}

export default new MessageHandler(); 