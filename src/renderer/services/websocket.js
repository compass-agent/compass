import io from 'socket.io-client';
import StateManager from './stateManager';

class WebSocketService {
  constructor() {
    this.socket = null;
  }

  connect() {
    this.socket = io('http://localhost:5001');

    this.socket.on('connect', () => {
      StateManager.setState('connection.connected', true);
    });

    this.socket.on('disconnect', () => {
      StateManager.setState('connection.connected', false);
    });

    this.socket.on('response', (data) => {
      if (data.type === 'ai') {
        const currentMessages = StateManager.getState('chat.messages');
        StateManager.setState('chat.messages', [...currentMessages, data]);
      }
    });

    this.socket.on('state_update', (data) => {
      StateManager.setState('agent', data);
    });

    this.socket.on('error', (error) => {
      StateManager.setState('chat.error', error.message);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }

  sendMessage(message) {
    if (this.socket) {
      this.socket.emit('message', { text: message });
      this.socket.emit('control_update', { playing: true });
    }
  }

  updateControlState(state) {
    if (this.socket) {
      this.socket.emit('control_update', state);
    }
  }
}

export default new WebSocketService(); 