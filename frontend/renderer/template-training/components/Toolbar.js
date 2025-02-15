import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faSave, 
  faTimes, 
  faObjectGroup,
  faWandMagicSparkles
} from '@fortawesome/free-solid-svg-icons';
import '../styles/components/Toolbar.scss';

const Toolbar = ({
  handleAnalyze,
  handleSaveTemplates,
  isAnalyzing,
  inputValue,
  setInputValue,
  handleKeyPress,
  selectedBox,
  onCancel,
  pageName,
  agentName
}) => {
  return (
    <div className="toolbar">
      <div className="toolbar-top">
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
            onClick={handleAnalyze}
            className="extract-button"
            disabled={isAnalyzing}
          >
            <FontAwesomeIcon icon={faObjectGroup} />
            {isAnalyzing ? 'Extracting...' : 'Extract Templates'}
          </button>
          <button 
            className="caption-all-button"
            disabled={selectedBox !== null}
          >
            <FontAwesomeIcon icon={faWandMagicSparkles} /> Caption All
          </button>
        </div>
      </div>
    </div>
  );
};

export default Toolbar; 