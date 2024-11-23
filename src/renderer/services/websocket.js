import io from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.stateHandlers = null;
  }

  setStateHandlers(handlers) {
    this.stateHandlers = handlers;
  }

  connect() {
    this.socket = io('http://localhost:5001');

    this.socket.on('connect', () => {
      this.stateHandlers?.onConnect();
    });

    this.socket.on('disconnect', () => {
      this.stateHandlers?.onDisconnect();
    });

    this.socket.on('response', (data) => {
      this.stateHandlers?.onResponse(data);
    });

    this.socket.on('state_update', (data) => {
      if (data && typeof data === 'object') {
        this.stateHandlers?.onStateUpdate({
          ...data,
          processing: data.processing ?? false,
          playing: data.playing ?? false
        });
      }
    });

    this.socket.on('error', (error) => {
      this.stateHandlers?.onError(error);
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
      this.socket.emit('message', { text: message });
    }
  }

  updateControlState(state) {
    if (this.socket?.connected) {
      this.socket.emit('control_update', state);
    }
  }
}

export default new WebSocketService(); 