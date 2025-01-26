import React, { useEffect, useRef } from "react";
import { Terminal } from "xterm";
import "xterm/css/xterm.css";
import "../../styles/workspace.scss";

const TerminalComponent = () => {
    const terminalRef = useRef(null); // Terminal container reference
    const xterm = useRef(null); // xterm.js instance reference
  
    // Initialize the terminal on mount
    useEffect(() => {
      xterm.current = new Terminal({
        cursorBlink: true,
        theme: {
          background: "#1e1e1e", // Terminal background
          foreground: "#ffffff", // Terminal text color
        },
      });
  
      // Attach the terminal to the container
      xterm.current.open(terminalRef.current);
  
      // Listen for command output from the main process
      const handleOutput = (data) => {
        xterm.current.writeln(data); // Write command output to the terminal
      };
      window.electron.terminal.onCommandOutput(handleOutput);
  
      // Cleanup listeners and terminal instance on unmount
      return () => {
        window.electron.terminal.removeCommandOutputListener(handleOutput);
        xterm.current.dispose();
      };
    }, []);
  
    // Function to handle command execution
    const handleCommandExecution = (command) => {
      if (!command.trim()) return; // Ignore empty commands
      xterm.current.writeln(`$ ${command}`); // Echo the entered command
      window.electron.terminal.runCommand(command); // Send the command to the backend
    };
  
    return (
      <div className="terminal-container" style={{ width: "100%", height: "100%" }}>
        {/* Terminal Display */}
        <div ref={terminalRef} className="xterm-wrapper" />
  
        {/* Command Input */}
        <div className="terminal-input">
          <input
            type="text"
            placeholder="Enter command"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleCommandExecution(e.target.value);
                e.target.value = ""; // Clear the input after executing the command
              }
            }}
          />
        </div>
      </div>
    );
  };
  
  export default TerminalComponent;
