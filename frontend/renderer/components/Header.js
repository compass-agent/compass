import React from 'react';
import '../styles/Header.css';

function Header() {
  const handleClose = () => {
    window.close();
  };

  const handleMinimize = () => {
    window.minimize();
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
      </div>
      <span className="title">Compass AI Assistant</span>
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