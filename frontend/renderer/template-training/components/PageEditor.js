import React from 'react';
import '../styles/components/PageEditor.scss';
import ImageWorkspace from './ImageWorkspace';
import Toolbar from './Toolbar';
import { useImageHandling } from '../hooks/useImageHandling';

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

  return (
    <div className="page-editor">
      <Toolbar
        handleAnalyze={() => handleAnalyze(getImageSrc(image))}
        handleSaveTemplates={() => handleSaveTemplates(getImageSrc(image))}
        isAnalyzing={isAnalyzing}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleKeyPress={handleKeyPress}
        selectedBox={selectedBox}
        onDeleteBox={() => deleteBox(selectedBox)}
        onCancel={() => setCurrentView(VIEW_STATES.PAGES_LIST)}
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