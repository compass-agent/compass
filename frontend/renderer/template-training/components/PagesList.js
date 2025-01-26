import React from 'react';
import '../styles/components/PagesList.scss';

const PagesList = ({ pages, onAddPage, onEditPage }) => {
  return (
    <div className="pages-list">
      <div className="pages-header">
        <h2>Pages</h2>
        <button className="primary" onClick={onAddPage}>
          Add New Page
        </button>
      </div>
      
      <div className="pages-container">
        {pages.length === 0 ? (
          <div className="empty-state">
            No pages added yet. Click "Add New Page" to get started.
          </div>
        ) : (
          <div className="pages-grid">
            {pages.map((page, index) => (
              <div key={index} className="page-card" onClick={() => onEditPage(index)}>
                {page.image && (
                  <div className="page-thumbnail">
                    <img src={page.image} alt={`Page ${index + 1}`} />
                  </div>
                )}
                <div className="page-info">
                  <span className="page-number">Page {index + 1}</span>
                  <span className="box-count">{page.boxes?.length || 0} boxes</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PagesList; 