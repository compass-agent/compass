const { spawn } = require("child_process");

function handleTerminalEvents(ipcMain) {
    ipcMain.on("run-command", (event, command) => {
      console.log("Main Process: Received command to run:", command);
  
      // Split the command into the executable and its arguments
      const [executable, ...args] = command.split(" ");
  
      const process = spawn(executable, args);
  
      // Send stdout back to the renderer process
      process.stdout.on("data", (data) => {
        console.log(`Command Output: ${data}`);
        event.sender.send("command-output", { type: "stdout", data: data.toString() });
      });
  
      // Send stderr back to the renderer process
      process.stderr.on("data", (data) => {
        console.error(`Command Error: ${data}`);
        event.sender.send("command-output", { type: "stderr", data: data.toString() });
      });
  
      // Notify renderer process when the command is complete
      process.on("close", (code) => {
        console.log(`Command exited with code ${code}`);
        event.sender.send("command-output", { type: "close", code });
      });
  
      // Handle any errors in spawning the process
      process.on("error", (error) => {
        console.error("Failed to run command:", error);
        event.sender.send("command-output", { type: "error", error: error.message });
      });
    });
  }
  
  module.exports = { handleTerminalEvents };