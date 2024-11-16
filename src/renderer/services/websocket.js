import io from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.messageHandlers = new Map();
  }

  connect() {
    this.socket = io('http://localhost:5001');

    this.socket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
    });

    this.socket.on('response', (data) => {
      if (this.messageHandlers.has('response')) {
        this.messageHandlers.get('response')(data);
      }
    });

    this.socket.on('state_update', (data) => {
      if (this.messageHandlers.has('state_update')) {
        this.messageHandlers.get('state_update')(data);
      }
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
    }
  }

  updateControlState(state) {
    if (this.socket) {
      this.socket.emit('control_update', state);
    }
  }

  onMessage(event, handler) {
    this.messageHandlers.set(event, handler);
  }
}

export default new WebSocketService(); 