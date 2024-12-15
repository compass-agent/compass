import React, { useState, useEffect } from "react";
import { useAppState } from '../context/AppContext';
import "../styles/Header.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faXmark,
  faWindowMinimize,
  faMinimize,
  faMaximize,
  faEllipsisVertical,
  faExpand,
  faCompress,
} from "@fortawesome/free-solid-svg-icons";
import { faSquare } from "@fortawesome/free-regular-svg-icons";

function Header() {
  const { state } = useAppState();
  const { compassWindow} = state;
  const [isFullscreen, setIsFullscreen] = useState(true);

  useEffect(() => {
    console.log(`Header: screenshot actionType ${ compassWindow.actionType}`);
    if (!compassWindow.actionType) {
      return;
    }
    if (compassWindow.actionType === 'minimize') {
      handleMinimize();
    } else if (compassWindow.actionType === 'restore') {
      window.electron.restoreWindow();
    }
  }, [compassWindow.actionType]);

  let isMac = window.electron.platform === "darwin";
  //isMac = true;
  const isWindows = window.electron.platform === "win32";
  console.log(`Header: start:  isMac ${isMac} isWindows ${isWindows}`);

  const handleClose = () => {
    if (window.electron && window.electron.closeWindow) {
      window.electron.closeWindow();
    } else {
      console.error("window.electron.closeWindow is not defined");
    }
  };

  const handleMinimize = () => {
    window.electron.minimizeWindow();
  };

  const handleToggleMaximizeWindow = () => {
    if (window.electron?.toggleMaximizeWindow) {
      window.electron.toggleMaximizeWindow();
    } else {
      console.error(
        "Renderer: window.electron.toggleMaximizeWindow is not defined"
      );
    }
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen((prev) => {
      const isNowFullscreen = !prev;
      const { ipcRenderer } = window.electron;
      if (ipcRenderer) {
        window.electron.ipcRenderer.send("toggle-fullscreen", isNowFullscreen);
      } else {
        console.error("ipcRenderer is not available");
      }

      return isNowFullscreen;
    });
  };

  const handleNewChat = () => {
    // TODO: Implement new chat functionality
    console.log("New chat clicked");
  };

  const handleShowSessions = () => {
    // TODO: Implement show sessions functionality
    console.log("Show sessions clicked");
  };

  const handleSettings = () => {
    // TODO: Implement settings functionality
    console.log("Settings clicked");
  };

  return (
    <div className={`header ${isMac ? "macos" : "windows"}`}>
      {/* Window Controls: Positioned on Left for MacOS and Right for Windows */}
      {isMac ? (
        <div className="window-controls left macos">
          {/* MacOS: Controls on the left */}
          <button
            className="window-control macos close"
            onClick={handleClose}
            title="Close"
          >
            {/* <FontAwesomeIcon icon={faXmark} /> */}
          </button>
          <button
            className="window-control macos max"
            onClick={handleToggleMaximizeWindow}
            title="Maximize"
          >
            {/* <FontAwesomeIcon icon={faSquare} /> */}
          </button>
          <button
            className="window-control macos min"
            onClick={handleMinimize}
            title="Minimize"
          >
            {/* <FontAwesomeIcon icon={faWindowMinimize} /> */}
          </button>
        </div>
      ) : (
        <div className="window-controls right ">
          {/* Windows: Menu on left, Close, Maximize, Minimize on right */}
          <button
            className="window-control minimize win"
            onClick={handleMinimize}
            title="Minimize"
          >
            <FontAwesomeIcon icon={faWindowMinimize} />
          </button>
          <button
            className="window-control win"
            onClick={handleToggleMaximizeWindow}
            title="Maximize"
          >
            <FontAwesomeIcon icon={faSquare} />
          </button>
          <button
            className="window-control win"
            onClick={handleClose}
            title="Close"
          >
            <FontAwesomeIcon icon={faXmark} />
          </button>
        </div>
      )}

      {/* Application Title and Icon: Always Centered */}
      <div className="title">
        {/* <img src="/path/to/icon.png" alt="App Icon" className="app-icon" /> */}
        {/* Compass */}
      </div>

      {/* Header Controls: Positioned on Right for MacOS and Left for Windows */}
      {isMac ? (
        <div className="header-controls right">
          {isFullscreen ? (
            <button
              className="header-button fullscreen"
              onClick={handleToggleFullscreen}
              title="Exit Fullscreen"
            >
              <FontAwesomeIcon icon={faCompress} />
            </button>
          ) : (
            <button
              className="header-button fullscreen"
              onClick={handleToggleFullscreen}
              title="Expand to Fullscreen"
            >
              <FontAwesomeIcon icon={faExpand} />
            </button>
          )}

          <button
            className="header-button settings"
            onClick={handleSettings}
            title="Settings"
          >
            <FontAwesomeIcon icon={faEllipsisVertical} />
          </button>
        </div>
      ) : (
        <div className="header-controls left">
          <button
            className="header-button settings"
            onClick={handleSettings}
            title="Settings"
          >
            <FontAwesomeIcon icon={faEllipsisVertical} />
          </button>
          {isFullscreen ? (
            <button
              className="header-button fullscreen"
              onClick={handleToggleFullscreen}
              title="Exit Fullscreen"
            >
              <FontAwesomeIcon icon={faCompress} />
            </button>
          ) : (
            <button
              className="header-button fullscreen"
              onClick={handleToggleFullscreen}
              title="Expand to Fullscreen"
            >
              <FontAwesomeIcon icon={faExpand} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default Header;
