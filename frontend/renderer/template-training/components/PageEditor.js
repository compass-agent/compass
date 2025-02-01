import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload, faCamera } from '@fortawesome/free-solid-svg-icons';
import '../styles/components/PageEditor.scss';
import ImageWorkspace from './ImageWorkspace';
import Toolbar from './Toolbar';
import { useImageHandling } from '../hooks/useImageHandling';
import WebSocketService from '../../common/services/websocket';
import { VIEW_STATES } from '../constants/viewStates';
import SaveDialog from './SaveDialog';

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
  setIsAnalyzing,
  currentScreenshot,
  agentName = "FreeCAD",
  handleAutoCaption
}) => {
  const [pageName, setPageName] = useState('');
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);

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

  useEffect(() => {
    if (currentScreenshot) {
      setImage(currentScreenshot.image);
      setPageName(currentScreenshot.page_name || '');
    }
  }, [currentScreenshot]);

  useEffect(() => {
    console.log('PageEditor boxes:', boxes);
  }, [boxes]);

  const handleSave = () => {
    if (!image) {
      alert('No image available');
      return;
    }

    if (Object.keys(captions).length === 0) {
      alert('No templates to save');
      return;
    }

    setIsSaveDialogOpen(true);
  };

  const handleFinalSave = (newPageName) => {
    const imageData = image.includes('base64,') 
      ? image.split('base64,')[1] 
      : image;

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
        page_name: newPageName.trim(),
        agent_name: agentName
      });
    });

    setIsSaveDialogOpen(false);
    setCurrentView(VIEW_STATES.PAGES_LIST);
  };

  const handleBoxChange = (boxId, newBox) => {
    setBoxes(prev => ({
      ...prev,
      [boxId]: newBox
    }));f 
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
        agentName={agentName}
      />

      <SaveDialog
        isOpen={isSaveDialogOpen}
        onClose={() => setIsSaveDialogOpen(false)}
        onSave={handleFinalSave}
        initialPageName={pageName}
        isExisting={!!currentScreenshot}
      />

      <div className="editor-content">
        {!image && !currentScreenshot ? (
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
                <FontAwesomeIcon icon={faUpload} /> Upload Image
              </label>
              <button 
                className="upload-button"
                onClick={() => {}}
                disabled
              >
                <FontAwesomeIcon icon={faCamera} /> Take Screenshot
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
            deleteBox={deleteBox}
            getImageSrc={getImageSrc}
            handleAutoCaption={handleAutoCaption}
            onBoxChange={handleBoxChange}
          />
        )}
      </div>
    </div>
  );
};

export default PageEditor; 