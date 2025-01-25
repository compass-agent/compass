import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch, faTrash, faSave, faTimes, faMagic } from '@fortawesome/free-solid-svg-icons';
import '../styles/components/Toolbar.scss';

const Toolbar = ({
  handleAnalyze,
  handleSaveTemplates,
  isAnalyzing,
  inputValue,
  setInputValue,
  handleKeyPress,
  selectedBox,
  onDeleteBox,
  onCancel,
  pageName,
  setPageName
}) => {
  return (
    <div className="toolbar">
      <div className="toolbar-top">
        <div className="left-actions">
          <input
            type="text"
            placeholder="Enter page name"
            value={pageName}
            onChange={(e) => setPageName(e.target.value)}
            className="page-name-input"
          />
          <button 
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="analyze-button"
          >
            <FontAwesomeIcon icon={faSearch} /> 
            {isAnalyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        
        <div className="right-actions">
          <button 
            onClick={onCancel}
            className="cancel-button"
          >
            <FontAwesomeIcon icon={faTimes} /> Cancel
          </button>
          <button 
            onClick={handleSaveTemplates}
            className="save-button"
            disabled={!pageName.trim()}
          >
            <FontAwesomeIcon icon={faSave} /> Save
          </button>
        </div>
      </div>

      <div className="toolbar-bottom">
        <textarea
          placeholder="Enter caption for selected box"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={selectedBox === null}
          rows={4}
        />
        <div className="box-actions">
          <button 
            onClick={onDeleteBox}
            disabled={selectedBox === null}
            className="delete-button"
          >
            <FontAwesomeIcon icon={faTrash} /> Delete Box
          </button>
          <button 
            disabled={selectedBox === null}
            className="auto-caption-button"
          >
            <FontAwesomeIcon icon={faMagic} /> Auto Caption
          </button>
        </div>
      </div>
    </div>
  );
};

export default Toolbar; 