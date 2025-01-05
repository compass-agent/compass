import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload, faSearch, faSave, faTrash } from '@fortawesome/free-solid-svg-icons';
import '../styles/components/Toolbar.scss';

const Toolbar = ({
  templateName,
  setTemplateName,
  handleImageUpload,
  handleAnalyze,
  isAnalyzing,
  inputValue,
  setInputValue,
  handleKeyPress,
  selectedBox,
  handleSaveTemplates,
  hasCaptions,
  onDeleteBox
}) => {
  const captionInputRef = React.useRef(null);

  React.useEffect(() => {
    if (selectedBox !== null && captionInputRef.current) {
      captionInputRef.current.focus();
    }
  }, [selectedBox]);

  return (
    <div className="toolbar">
      <input
        type="text"
        placeholder="Template Name"
        value={templateName}
        onChange={(e) => setTemplateName(e.target.value)}
      />
      <button onClick={() => document.getElementById('imageUpload').click()}>
        <FontAwesomeIcon icon={faUpload} /> Upload Image
      </button>
      <input
        id="imageUpload"
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        style={{ display: 'none' }}
      />
      <button 
        onClick={handleAnalyze}
        disabled={isAnalyzing}
      >
        <FontAwesomeIcon icon={faSearch} /> 
        {isAnalyzing ? 'Analyzing...' : 'Analyze'}
      </button>
      <input
        ref={captionInputRef}
        type="text"
        placeholder="Enter caption for selected box"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        style={{ 
          width: '300px',
          border: selectedBox !== null ? '2px solid #ff0000' : '1px solid #444'
        }}
      />
      <button 
        onClick={handleSaveTemplates}
        disabled={!hasCaptions}
      >
        <FontAwesomeIcon icon={faSave} /> Save All Templates
      </button>
      <button 
        onClick={() => {
          console.log('Delete button clicked, selectedBox:', selectedBox);
          onDeleteBox();
        }}
        disabled={selectedBox === null}
        className="delete-button"
      >
        <FontAwesomeIcon icon={faTrash} /> Delete Box
      </button>
    </div>
  );
};

export default Toolbar; 