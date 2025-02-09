import React, { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";
import "../../styles/workspace.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faXmark,
  faFolderOpen,
  faPlus,
  faTerminal,
} from "@fortawesome/free-solid-svg-icons";
import { parseTerminalCommand, isPrintableASCII } from "../../utils/utils";
import { v4 as uuidv4 } from "uuid";

const TerminalComponent = ({ tabs, terminalWidth, setTabs }) => {
  const terminalRefs = useRef(new Map()); // Stores terminal instances (id, term)
  const containerRefs = useRef(new Map()); // Stores container elements for each tab (id, DOM)
  const [canAddTab, setCanAddTab] = useState(true);
  const tabsRef = useRef([]); // Refs to measure individual tab widths
  const [activeTabId, setActiveTabId] = useState(
    tabs.length > 0 ? tabs[0].id : ""
  );
  //const terminalRef = useRef(null); //c
  //Initialize terminals when tabs are updated
  useEffect(() => {
    console.log("Terminal: Initialize tabs:", { tabs });
    tabs.forEach(async (tab) => {
      if (!terminalRefs.current.has(tab.id)) {
        console.log("Terminal: createTerminal :");
        await createTerminal(tab);
      }
    });

    // Update refs when tabs change
    tabsRef.current = tabsRef.current.slice(0, tabs.length);
    updateCanAddTab(); // Check tab accumulation on tabs update
  }, [tabs]);

  const createTerminal = async (tab) => {
    if (!tabs || tabs.length === 0) return;
    const { id, command, isInitial } = tab;
    console.log("Initializing terminal for:", tab);

    const term = new Terminal({
      cursorBlink: true,
      theme: { background: "#1e1e1e", foreground: "#ffffff" },
      wordWrap: true,
      allowTransparency: true,
      scrollback: 1000,
      cols: 180, // ✅ Set a fixed column width for better wrapping
      convertEol: true, // ✅ Ensures new lines are properly handled

    });

    const container = containerRefs.current.get(id);
    if (container) {
      term.open(container);
      term.focus();
    } else {
      console.error(`Container for terminal ${id} not found.`);
      return;
    }

    // Initialize command buffer with the command from the tab
    let commandBuffer = parseTerminalCommand(command) || "";
    let isFirst = true;
    // Create terminal session
    window.electron.terminal
      .create({ id: id, command: commandBuffer })
      .then((response) => {
        if (response.success) {
          console.log(`Terminal ${id} successfully with command: ${commandBuffer}`);

          window.electron.terminal.onOutput(id, (data) => {
            console.log(
              `Output tab.isInitial && isFirst ${
                tab.isInitial
              } ${isFirst} Data  ${data.toString()}`
            );
            // Check when the PowerShell prompt appears
            const arg = `${data} ${
              isInitial && isFirst && data.includes(">")
                ? commandBuffer
                : ""
            }`;
            term.write("\r\n");
            term.write(arg);
            isFirst = false;
          });

          window.electron.terminal.onError(id, (data) => {
            console.log(`Terminal Error for ${id}: ${data}`);
            term.write("\r\n");
            const errorData = `\x1b[31m${data}\x1b[0m`;
            term.write(errorData); // Write error data in red
          });
        } else {
          console.error(`Failed to create terminal with ID ${id}`);
        }
      });

    // Handle user input
    term.onData((data) => {
      console.log(`User input in terminal ${id}: ${data}, buffer: ${commandBuffer}`);

      if (data === "\r") {
        // User pressed Enter: send the command
        console.log(`Executing command in terminal: ${commandBuffer}`);
        term.write("\r\n");
        window.electron.terminal.input({
          id: id,
          input: commandBuffer + "\n",
        });
        commandBuffer = "";
      } else if (data === "\u0003") {
        // User pressed Ctrl + C (ASCII `\u0003`)
        console.log(`Ctrl + C in terminal ${id}. Stopping process.`);
        window.electron.terminal.sendSignal(id, "SIGINT");
        term.write("^C\r\n"); // Display ^C and move to a new line
        commandBuffer = "";
      } else if (data === "\u007F") {
        // Handle backspace
        if (commandBuffer.length > 0) {
          commandBuffer = commandBuffer.slice(0, -1);
          term.write("\b \b"); // Erase the last character visually
        }
      } else if (isPrintableASCII(data)) {
        // Append to command buffer
        commandBuffer += data;
        term.write(data); // Echo the character
      }
    });
  };

  const addNewTab = async () => {
    // new UI terminal 
    // call Create with new id (check id works for all Term separately in backend)
    console.info(`addNewTab in`);
    const id = `term-${tabs.length + 1}-${uuidv4()}`;
    const newTab = { id, name: `Terminal ${tabs.length + 1}`, command: "", isInitial: false };
    const { success } = await window.electron.terminal.create({id});
    console.info(`addNewTab success`);
    if (success) {
      setTabs([...tabs, newTab]); // Add the new tab to the UI
      setActiveTabId(id); // Switch to the new tab
      await createTerminal(newTab); // Create the frontend terminal instance
      console.info(`addNewTab after await newTab: ${newTab}`);
    } else {
      console.error(`Failed to create terminal with ID ${id}`);
    }
  };

  const handleTabClick = (id) => {
    setActiveTabId(id);
  };


  const closeTab = (id) => {
    setTabs((prev) => prev.filter((tab) => tab.id !== id));
    window.electron.terminal.close(id);
    terminalRefs.current.get(id)?.dispose();
    terminalRefs.current.delete(id);
    console.info(`closeTab after await newTab: ${id} activeID: ${activeTabId}`);
    let activeTabId = id;

    if (tabs.length === 0) return;
    if (id === activeTabId ) {
      const remainingTabs = tabs.filter((tab) => tab.id !== id);
      console.info(`closeTab setActivetab : ${remainingTabs.length - 1}`);
      activeTabId = remainingTabs[remainingTabs.length - 1]?.id;
    }

    setTimeout(() => {
      setActiveTabId(activeTabId || "");
    }, 0);
  };

  const updateCanAddTab = () => {
    const panelWidth = terminalWidth || 0;
    const totalTabWidth = tabsRef.current.reduce(
      (acc, tab) => acc + (tab?.offsetWidth || 0),
      0
    );
    console.log(
      "Terminal - updateCanAddTab: panelWidth totalTabWidth",
      panelWidth,
      totalTabWidth
    );
    setCanAddTab(totalTabWidth + 120 <= panelWidth); // 100px for a new tab
  };

  return (
    <div className="terminal-wrapper">
      <div className="tabs">
        {tabs.map((tab, index) => (
          <div
            key={tab.id}
            ref={(el) => (tabsRef.current[index] = el)} // Assign ref for each tab
            className={`tab ${
              tab.id === activeTabId ? "active" : ""
            }`}
            onClick={() => handleTabClick(tab.id)}
          >
            <span className="tab-label">{tab.name}</span>
            <button
              onClick={() => closeTab(tab.id)}
              className="close-tab-btn"
              title="Close tab"
            >
              <FontAwesomeIcon icon={faXmark} />
            </button>
          </div>
        ))}
        {canAddTab && (
          <button
            onClick={addNewTab}
            className="add-tab-btn"
            title="Add terminal"
          >
            <FontAwesomeIcon icon={faPlus} />
          </button>
        )}
      </div>

      {/* Terminal View Section */}
      <div className="terminal-views">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className="terminal-view"
            style={{ display: tab.id === activeTabId ? "block" : "none" }}
            ref={(el) => containerRefs.current.set(tab.id, el)}
          />
        ))}
      </div>
    </div>
  );
};

export default TerminalComponent;
