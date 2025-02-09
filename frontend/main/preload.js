const { contextBridge, ipcRenderer } = require("electron");

// Expose specific APIs to the renderer process via the `window` object
//ipcRenderer.send: Sends messages from the renderer process to the main process.

contextBridge.exposeInMainWorld("electron", {
  platform: process.platform,
  ipcRenderer: {
    send: (channel, data) => {
      const validChannels = [
        "toggle-fullscreen",
        "move-to-bottom-right",
        "close-window",
        "minimize-window",
        "maximize-window",
        "show-coordinate-preview",
        "hide-coordinate-preview",
        "open-template-training",
        "open-file-editor",
        "save-file-content",
        "close-editor-window",
      ];
      if (validChannels.includes(channel)) {
        if (
          channel !== "toggle-fullscreen" &&
          channel !== "move-to-bottom-right"
        ) {
          ipcRenderer.send(channel, data);
        }
      }
    },
    on: (channel, func) => {
      const validChannels = [
        "move-to-bottom-right-done",
        "load-file-content",
        "save-file-success",
        "terminal.output",
      ];
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (event, ...args) => func(...args));
      }
    },
    invoke: (channel, data) => {
      const validChannels = [
        "open-file-dialog",
        "save-file",
        "read-file",
        "save-file-dialog",
        "terminal.create",
        "terminal.resize",
        "terminal.input",
        "terminal.close",
      ];
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, data);
      }
    },
    removeListener: (channel, func) => {
      const validChannels = [
        "move-to-bottom-right-done",
        "load-file-content",
        "save-file-success",
      ];
      if (validChannels.includes(channel)) {
        ipcRenderer.removeListener(channel, func);
      }
    },
  },
  restoreWindow: () => ipcRenderer.send("restore-window"),
  closeWindow: () => ipcRenderer.send("close-window"),
  minimizeWindow: () => ipcRenderer.send("minimize-window"),
  toggleMaximizeWindow: () => ipcRenderer.send("maximize-window"), // Expose toggle function
  templateTraining: {
    saveTemplate: (data) => ipcRenderer.send("save-template", data),
    onTemplateSaved: (callback) => ipcRenderer.on("template-saved", callback),
  },
  terminal: {
    create: ({id, command}) => ipcRenderer.invoke("terminal.create", {id, command}),
    input: ({id, input}) => ipcRenderer.invoke("terminal.input", { id, input }),
    sendSignal: (id, signal) => ipcRenderer.invoke("terminal.sendSignal", { id, signal }),
    close: (id) => ipcRenderer.invoke("terminal.close", id),
    kill: (id) => ipcRenderer.invoke("terminal.kill", id),
    onOutput: (id, callback) => {
      if (typeof callback !== "function") {
        console.error(`Invalid callback provided to onOutput for terminal ${id}`);
        return;
      }
      ipcRenderer.on(`terminal.output.${id}`, (event, data) => callback(data))},
    onError: (id, callback) =>
      ipcRenderer.on(`terminal.error.${id}`, (event, data) => callback(data)),
  },
});

// Add coordinate preview API
contextBridge.exposeInMainWorld("coordinatePreview", {
  showPreview: (x, y) => ipcRenderer.send("show-coordinate-preview", { x, y }),
  hidePreview: () => ipcRenderer.send("hide-coordinate-preview"),
});
