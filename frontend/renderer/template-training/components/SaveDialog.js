import React, { useState } from 'react';
import '../styles/components/SaveDialog.scss';

const SaveDialog = ({ isOpen, onClose, onSave, initialPageName, isExisting }) => {
  const [pageName, setPageName] = useState(initialPageName || '');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!pageName.trim()) return;
    onSave(pageName);
  };

  return (
    <div className="save-dialog-overlay">
      <div className="save-dialog">
        <h2>{isExisting ? 'Update Page' : 'Save New Page'}</h2>
        {isExisting && (
          <p className="warning">
            Warning: This will update the existing page "{initialPageName}".
          </p>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="pageName">Page Name:</label>
            <input
              type="text"
              id="pageName"
              value={pageName}
              onChange={(e) => setPageName(e.target.value)}
              placeholder="Enter page name"
              required
            />
          </div>
          <div className="dialog-actions">
            <button type="button" className="cancel-button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="save-button">
              {isExisting ? 'Update' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SaveDialog; 