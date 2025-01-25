import React, { useState } from 'react';
import '../styles/components/PageEditor.scss';
import ImageWorkspace from './ImageWorkspace';
import Toolbar from './Toolbar';
import { useImageHandling } from '../hooks/useImageHandling';
import WebSocketService from '../../common/services/websocket';
import { VIEW_STATES } from '../constants/viewStates';

const PageEditor = ({ 
  onSave, 
  onCancel, 
  handleAnalyze,
  handleSaveTemplates,
  isAnalyzing,
  boxes,
  selectedBox,
  handleBoxClick,
  createNewBox,
  deleteBox,
  inputValue,
  setInputValue,
  handleKeyPress,
  captions,
  setCurrentView,
  setDetections,
  setBoxes,
  setCaptions,
  setSelectedBox,
  setIsAnalyzing
}) => {
  const [pageName, setPageName] = useState('');

  const cleanupFunctions = {
    setDetections,
    setBoxes,
    setCaptions,
    setSelectedBox,
    setIsAnalyzing
  };

  const {
    image,
    setImage,
    imageSize,
    handleImageLoad,
    handleImageUpload,
    getImageSrc
  } = useImageHandling(cleanupFunctions);

  const handleSave = () => {
    if (!image) {
      alert('No image available');
      return;
    }

    if (!pageName.trim()) {
      alert('Please enter a page name');
      return;
    }

    if (Object.keys(captions).length === 0) {
      alert('No templates to save');
      return;
    }

    // Remove the data URL prefix if it exists
    const imageData = image.includes('base64,') 
      ? image.split('base64,')[1] 
      : image;

    // Save each box as a template
    Object.entries(captions).forEach(([boxIndex, caption]) => {
      const box = boxes[boxIndex];
      if (!box) return;

      const bbox = [
        box.x,
        box.y,
        box.x + box.width,
        box.y + box.height
      ];

      WebSocketService.saveTemplate({
        image: imageData,
        caption: caption,
        bbox: bbox,
        page_name: pageName.trim()
      });
    });

    // Return to pages list
    setCurrentView(VIEW_STATES.PAGES_LIST);
  };

  return (
    <div className="page-editor">
      <Toolbar
        handleAnalyze={() => handleAnalyze(image)}
        handleSaveTemplates={handleSave}
        isAnalyzing={isAnalyzing}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleKeyPress={handleKeyPress}
        selectedBox={selectedBox}
        onDeleteBox={() => deleteBox(selectedBox)}
        onCancel={() => setCurrentView(VIEW_STATES.PAGES_LIST)}
        pageName={pageName}
        setPageName={setPageName}
      />

      <div className="editor-content">
        {!image ? (
          <div className="upload-area">
            <div className="upload-buttons">
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
              <button 
                className="upload-button"
                onClick={() => {}}
                disabled
              >
                Take Screenshot
              </button>
            </div>
            <div className="upload-instructions">
              Upload an image or take a screenshot to begin
            </div>
          </div>
        ) : (
          <ImageWorkspace
            image={image}
            handleImageLoad={handleImageLoad}
            imageSize={imageSize}
            boxes={boxes}
            selectedBox={selectedBox}
            captions={captions}
            handleBoxClick={handleBoxClick}
            createNewBox={createNewBox}
            getImageSrc={getImageSrc}
          />
        )}
      </div>
    </div>
  );
};

export default PageEditor; 