import React, { useState } from 'react';
import '../styles/components/PageEditor.scss';
import ImageWorkspace from './ImageWorkspace';

const PageEditor = ({ 
  onSave, 
  onCancel, 
  handleAnalyze,
  handleSaveTemplates,
  isAnalyzing,
  image,
  setImage,
  boxes,
  selectedBox,
  handleBoxClick,
  createNewBox,
  deleteBox,
  inputValue,
  setInputValue,
  handleKeyPress,
  captions,
  imageSize,
  handleImageLoad,
  detections
}) => {

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageData = e.target.result;
        setImage(imageData);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="page-editor">
      <div className="editor-header">
        <h2>Add New Page</h2>
        <div className="header-actions">
          <button 
            className="primary"
            onClick={handleAnalyze}
            disabled={!image || isAnalyzing}
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze'}
          </button>
          <button className="secondary" onClick={onCancel}>
            Cancel
          </button>
          <button 
            className="primary" 
            onClick={handleSaveTemplates}
            disabled={!image || Object.keys(boxes).length === 0}
          >
            Save Templates
          </button>
        </div>
      </div>

      <div className="editor-content">
        {!image ? (
          <div className="upload-area">
            <input
              type="file"
              id="imageUpload"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ display: 'none' }}
            />
            <label htmlFor="imageUpload" className="upload-button">
              Upload Image
            </label>
            <button className="upload-button disabled" disabled>
              Take Screenshot
            </button>
          </div>
        ) : (
          <ImageWorkspace
            image={image}
            handleImageLoad={handleImageLoad}
            detections={detections}
            boxes={boxes}
            imageSize={imageSize}
            selectedBox={selectedBox}
            captions={captions}
            handleBoxClick={handleBoxClick}
            createNewBox={createNewBox}
          />
        )}
      </div>
    </div>
  );
};

export default PageEditor; 