import React, { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronRight } from '@fortawesome/free-solid-svg-icons';
import WebSocketService from '../../common/services/websocket';
import '../styles/components/PagesList.scss';

const PagesList = ({ agentName, onAddPage, onEditPage }) => {
  const [pages, setPages] = useState([]);

  useEffect(() => {
    // Set up WebSocket handler for pages list
    WebSocketService.setStateHandlers({
      ...WebSocketService.stateHandlers,
      onScreenshotsList: (data) => {
        setPages(data.screenshots || []);
      }
    });

    // Get initial pages
    if (agentName) {
      WebSocketService.getScreenshots(agentName);
    }
  }, [agentName]);

  return (
    <div className="pages-list">
      <div className="navigation-path">
        <span className="agent-name">{agentName}</span>
        <FontAwesomeIcon icon={faChevronRight} className="path-separator" />
        <span className="page-name">Pages</span>
      </div>

      <div className="pages-header">
        <h2>Pages</h2>
      </div>
      
      <div className="pages-container">
        <div className="pages-grid">
          {/* Add New Card */}
          <div className="page-card add-card" onClick={onAddPage}>
            <div className="add-icon">+</div>
            <span>Add New Page</span>
          </div>

          {/* Existing Pages */}
          {pages.map((page) => (
            <div 
              key={page.id} 
              className="page-card" 
              onClick={() => onEditPage(page)}
            >
              <div className="page-thumbnail">
                <img 
                  src={`data:image/png;base64,${page.image}`} 
                  alt={page.name || `Page ${page.id}`} 
                />
              </div>
              <div className="page-info">
                <span className="page-name">{page.name || 'Untitled'}</span>
                <span className="page-date">
                  {new Date(page.created_at).toLocaleDateString()}
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