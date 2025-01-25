import React, { useEffect, useState } from 'react';
import WebSocketService from '../../common/services/websocket';
import '../styles/components/PagesList.scss';

const PagesList = ({ agentName, onAddPage, onEditPage }) => {
  const [screenshots, setScreenshots] = useState([]);

  useEffect(() => {
    // Set up WebSocket handler for screenshots list
    WebSocketService.setStateHandlers({
      ...WebSocketService.stateHandlers,
      onScreenshotsList: (data) => {
        setScreenshots(data.screenshots || []);
      }
    });

    // Get initial screenshots
    if (agentName) {
      WebSocketService.getScreenshots(agentName);
    }
  }, [agentName]);

  return (
    <div className="pages-list">
      <div className="pages-header">
        <h2>Screenshots</h2>
        <button className="primary" onClick={onAddPage}>
          Add New Screenshot
        </button>
      </div>
      
      <div className="pages-container">
        <div className="pages-grid">
          {/* Add New Card */}
          <div className="page-card add-card" onClick={onAddPage}>
            <div className="add-icon">+</div>
            <span>Add New Screenshot</span>
          </div>

          {/* Existing Screenshots */}
          {screenshots.map((screenshot) => (
            <div 
              key={screenshot.id} 
              className="page-card" 
              onClick={() => onEditPage(screenshot)}
            >
              <div className="page-thumbnail">
                <img 
                  src={`data:image/png;base64,${screenshot.image}`} 
                  alt={`Screenshot ${screenshot.id}`} 
                />
              </div>
              <div className="page-info">
                <span className="page-date">
                  {new Date(screenshot.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PagesList; 