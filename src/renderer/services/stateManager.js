class StateManager {
  constructor() {
    this.listeners = new Map();
    this.state = {
      connection: {
        isConnected: false,
        isReconnecting: false,
        error: null
      },
      agent: {
        isAutoMode: false,
        isHighlightMode: false,
        isPlaying: false,
        isProcessing: false,
        currentTask: null
      },
      chat: {
        messages: [],
        isTyping: false,
        error: null
      }
    };
  }

  setState(path, value) {
    const parts = path.split('.');
    let current = this.state;
    for (let i = 0; i < parts.length - 1; i++) {
      current = current[parts[i]];
    }
    current[parts[parts.length - 1]] = value;

    this.notifyListeners(path);
  }

  getState(path) {
    const parts = path.split('.');
    let current = this.state;
    for (const part of parts) {
      current = current[part];
    }
    return current;
  }

  subscribe(path, listener) {
    if (!this.listeners.has(path)) {
      this.listeners.set(path, new Set());
    }
    this.listeners.get(path).add(listener);

    return () => {
      this.listeners.get(path).delete(listener);
    };
  }

  notifyListeners(path) {
    if (this.listeners.has(path)) {
      const value = this.getState(path);
      this.listeners.get(path).forEach(listener => listener(value));
    }
  }
}

export default new StateManager(); 