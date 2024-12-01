import React from 'react';
import '../styles/Header.scss';

function Header() {
  const handleClose = () => {
    if (window.electron && window.electron.closeWindow) {
      window.electron.closeWindow(); // Call the exposed method
    } else {
      console.error('window.electron.closeWindow is not defined');
    }
  };

  const handleMinimize = () => {
    window.electron.minimizeWindow();
  };

  const handleToggleMaximizeWindow = () => {
    if (window.electron?.toggleMaximizeWindow) {
      window.electron.toggleMaximizeWindow(); // Use the toggle function
    } else {
      console.error('Renderer: window.electron.toggleMaximizeWindow is not defined');
    }
  };

  const handleNewChat = () => {
    // TODO: Implement new chat functionality
    console.log('New chat clicked');
  };

  const handleShowSessions = () => {
    // TODO: Implement show sessions functionality
    console.log('Show sessions clicked');
  };

  const handleSettings = () => {
    // TODO: Implement settings functionality
    console.log('Settings clicked');
  };

  return (
    <div className="header">
      <div className="window-controls">
        <button className="window-control close" onClick={handleClose}>✕</button>
        <button className="window-control minimize" onClick={handleMinimize}>−</button>
        <button className="window-control maximize" onClick={handleToggleMaximizeWindow}>⬜</button>
      </div>
      <span className="title">Compass</span>
      <div className="header-controls">
        <button className="header-button" onClick={handleSettings} title="Settings">
          ⚙️
        </button>
        <button className="header-button" onClick={handleShowSessions} title="Chat Sessions">
          💬
        </button>
        <button className="header-button new-chat" onClick={handleNewChat} title="New Chat">
          ✨
        </button>
      </div>
    </div>
  );
}

export default Header; 