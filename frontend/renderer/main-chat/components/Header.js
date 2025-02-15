import React, { useState, useEffect } from "react";
import { useAppState } from "../../common/context/AppContext";
import "../styles/Header.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faXmark,
  faWindowMinimize,
  faMinimize,
  faMaximize,
  faEllipsisVertical,
  faUsersCog,
  faExpand,
  faCompress,
  faUpRightAndDownLeftFromCenter,
  faMinus,
  faImage,
  faMessage,
  faArrowsRotate,
  faRobot,
  faEdit,
} from "@fortawesome/free-solid-svg-icons";
import { faSquare } from "@fortawesome/free-regular-svg-icons";
import WebSocketService from "../../common/services/websocket";
import SettingsMenu from "./SettingsMenu";

function Header() {
  const { state } = useAppState();
  const { compassWindow } = state;
  const [isFullscreen, setIsFullscreen] = useState(true);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);

  let isMac = window.electron.platform === "darwin";
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
    const selectedAgentName = state.selectedAgentName || "FreeCAD"; // Default fallback
    WebSocketService.handleNewChat(selectedAgentName);
  };

  const handleShowSessions = () => {
    // TODO: Implement show sessions functionality
    console.log("Show sessions clicked");
  };

  const handleSettings = () => {
    // TODO: Implement settings functionality
    console.log("Settings clicked");
  };

  const handleTemplateTraining = () => {
    console.log("Template training button clicked");
    window.electron.ipcRenderer.send("open-template-training");
  };

  const handleSettingsClick = (e) => {
    e.stopPropagation();
    setShowSettingsMenu(!showSettingsMenu);
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setShowSettingsMenu(false);
    };

    if (showSettingsMenu) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showSettingsMenu]);

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
            <FontAwesomeIcon icon={faXmark} />
          </button>
          <button
            className="window-control macos min"
            onClick={handleMinimize}
            title="Minimize"
          >
            <FontAwesomeIcon icon={faMinus} />
          </button>
          <button
            className="window-control macos max"
            onClick={handleToggleMaximizeWindow}
            title="Maximize"
          >
            <FontAwesomeIcon icon={faUpRightAndDownLeftFromCenter} />
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

          <div className="settings-container">
            <button
              className="header-button settings"
              onClick={handleSettingsClick}
              title="Settings"
            >
              <FontAwesomeIcon icon={faUsersCog} />
            </button>

            {showSettingsMenu && (
              <SettingsMenu onClose={() => setShowSettingsMenu(false)} />
            )}
          </div>

          <button
            className="header-button"
            onClick={handleNewChat}
            title="New Chat"
          >
            <FontAwesomeIcon icon={faArrowsRotate} />
          </button>
        </div>
      ) : (
        <div className="header-controls left">
          <div className="settings-container">
            <button
              className="header-button settings"
              onClick={handleSettingsClick}
              title="Settings"
            >
              <FontAwesomeIcon icon={faUsersCog} />
            </button>

            {showSettingsMenu && (
              <SettingsMenu onClose={() => setShowSettingsMenu(false)} />
            )}
          </div>
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
            className="header-button"
            onClick={handleNewChat}
            title="New Chat"
          >
            <FontAwesomeIcon icon={faArrowsRotate} />
          </button>
        </div>
      )}
    </div>
  );
}

export default Header;
