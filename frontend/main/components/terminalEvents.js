const { spawn } = require("child_process");
require("dotenv").config();

// Known PowerShell startup messages to filter out
const startupMessages = [
  "Windows PowerShell",
  "Copyright (C) Microsoft Corporation. All rights reserved.",
  "Try the new cross-platform PowerShell https://aka.ms/pscore6",
];

// Store terminal instances and logs
let terminals = {}; // Store terminal instances by ID
const lastOutputs = {};
const shell = process.platform === "win32" ? "powershell.exe" : "/bin/bash";
function handleTerminalEvents(ipcMain) {

  // Handle terminal creation
  ipcMain.handle("terminal.create", (event, { id, command }) => {
    // TODO: The command should be removed
    console.log("Main Terminal: terminal.create: command: ", command);
    if (terminals[id]) {
      terminals[id].kill();
    }

    const terminalProcess = spawn(shell, [], {
      shell: true,
      env: process.env,
    });

    terminals[id] = terminalProcess; // Store the terminal instance

    // Send terminal output to the renderer
    terminalProcess.stdout.on("data", (data) => {
      const output = data.toString().trim();
      console.log(`Main Terminal: terminal.create output ${output}`);
      if (
        output.length === 0 ||
        output === lastOutputs[id] ||
        startupMessages.some((msg) => output.includes(msg))
      )
        return;
      lastOutputs[id] = output;
      event.sender.send(`terminal.output.${id}`, output);
    });

    terminalProcess.stderr.on("data", (data) => {
      const errorOutput = data.toString().trim();
      if (errorOutput.length === 0) return;
      console.log(`Main Terminal: terminal.stderr output  ${errorOutput}`);
      event.sender.send(`terminal.error.${id}`, errorOutput);
    });

    // terminalProcess.on("close", () => {
    //   console.log("Main Terminal: close");
    //   delete terminals[id];
    //   delete lastOutputs[id]; 
    // });

    return { success: true };
  });

  // Handle user input from renderer
  ipcMain.handle("terminal.input", (event, { id, input }) => {
    console.log(`Main Terminal: received input -> ${input} for ${id}`);
    const terminalProcess = terminals[id];
    if (!terminalProcess) {
      console.error(`Terminal ${id} not found.`);
      return { success: false, error: "Terminal not found" };
    }
    if (input.trim()) {
      terminalProcess.stdin.write(input + "\n");
      console.log(`Main Terminal: write -> ${input}`);
      return { success: true };
    } else {
      console.error(`Received empty input for terminal ${id}`);
      return { success: false, error: "Empty input" };
    }
  });

  //Handle terminal closing
  ipcMain.handle("terminal.close", (event, id) => {
    console.log("Main Terminal: close");
    const terminalProcess = terminals[id];
    if (terminalProcess) {
      terminalProcess.kill();
      delete terminals[id];
      delete lastOutputs[id];

      return { success: true };
    }
    return { success: false };
  });

  ipcMain.handle("terminal.sendSignal", (event, { id, signal }) => {
    console.log(`Main Terminal: sending signal -> ${signal} to terminal ${id}`);
    const terminalProcess = terminals[id];
    if (terminalProcess) {
      terminalProcess.kill(signal);
      if (signal === 'SIGINT') {
        event.sender.send(`terminal.output.${id}`, `PS ${process.cwd()}>`);
      }
      return { success: true };
    }
    return { success: false, error: "Terminal not found" };
  });

  ipcMain.handle("terminal.kill", (event, id) => {
    console.log(`Killing terminal process ${id}`);
    const terminalProcess = terminals[id];
    if (terminalProcess) {
      try {
        if (process.platform === "win32") {
          // Windows: Use `taskkill` to stop the process
          spawn("taskkill", ["/PID", terminalProcess.pid, "/F"]);
        } else {
          // macOS & Linux: Send SIGINT (Ctrl+C equivalent)
          terminalProcess.kill("SIGINT");
        }
        delete terminals[id];
        delete lastOutputs[id];
        return { success: true };
      } catch (error) {
        console.error(`Error killing terminal ${id}:`, error);
        return { success: false, error };
      }
    }
    return { success: false, error: "Terminal not found" };
  });
}

module.exports = { handleTerminalEvents };
