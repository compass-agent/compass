import React, { useEffect, useState } from 'react';
import WebSocketService from '../../common/services/websocket';
import '../styles/components/PagesList.scss';

const PagesList = ({ agentName, onAddPage, onEditPage }) => {
  const [pages, setPages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    console.log('PagesList useEffect running for agent:', agentName);
    setIsLoading(true);

    const screenshotsHandler = (data) => {
      console.log('🎯 Screenshots handler called with data:', data);
      try {
        if (data && Array.isArray(data.screenshots)) {
          console.log('✅ Valid screenshots data received:', data.screenshots);
          setPages(data.screenshots);
        } else {
          console.warn('⚠️ Invalid screenshots data format:', data);
          setPages([]);
        }
      } catch (error) {
        console.error('❌ Error handling screenshots data:', error);
        setPages([]);
      } finally {
        console.log('🏁 Setting loading state to false');
        setIsLoading(false);
      }
    };

    // Set up the handler immediately
    WebSocketService.stateHandlers.onScreenshotsList = new Set([screenshotsHandler]);

    // Request screenshots if we have an agent name
    if (agentName) {
      console.log('🔍 Requesting screenshots for agent:', agentName);
      WebSocketService.getScreenshots(agentName);
    } else {
      console.log('⚠️ No agent name provided, clearing loading state');
      setIsLoading(false);
    }

    // Cleanup handler when component unmounts
    return () => {
      WebSocketService.stateHandlers.onScreenshotsList.clear();
    };
  }, [agentName]);

  // Debug logging for state changes
  useEffect(() => {
    console.log('🔄 Loading state changed to:', isLoading);
  }, [isLoading]);

  useEffect(() => {
    console.log('📄 Pages state updated:', pages);
  }, [pages]);

  if (isLoading) {
    return (
      <div className="pages-list">
        <div>Loading pages for agent: {agentName}...</div>
        <div>Current pages count: {pages.length}</div>
        <div>Handler count: {WebSocketService.stateHandlers.onScreenshotsList.size}</div>
      </div>
    );
  }

  return (
    <div className="pages-list">
      <div className="pages-header">
        <h2>Pages ({pages.length})</h2>
      </div>
      
      <div className="pages-container">
        <div className="pages-grid">
          {pages.length === 0 ? (
            <div className="no-pages">No pages found for this agent</div>
          ) : (
            <>
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
            </>
          )}

          <div className="page-card add-card" onClick={onAddPage}>
            <div className="add-icon">+</div>
            <span>Add New Page</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PagesList; 