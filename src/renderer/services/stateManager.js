class StateManager {
  constructor() {
    this.listeners = new Map();
    this.state = {
      connection: {
        connected: false,
        reconnecting: false,
        error: null
      },
      agent: {
        autoMode: false,
        highlightMode: false,
        playing: false,
        processing: false,
        currentTask: null
      },
      chat: {
        messages: [],
        error: null,
        currentInput: ''
      }
    };
  }

  setState(path, value) {
    const parts = path.split('.');
    let current = this.state;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!(parts[i] in current)) {
        current[parts[i]] = {};
      }
      current = current[parts[i]];
    }
    const key = parts[parts.length - 1];
    if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
      current[key] = { ...current[key], ...value };
    } else {
      current[key] = value;
    }

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