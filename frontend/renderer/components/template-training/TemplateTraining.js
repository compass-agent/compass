import React, { useState, useEffect } from 'react';
import Toolbar from './components/Toolbar';
import ImageWorkspace from './components/ImageWorkspace';
import { useSocketConnection } from './hooks/useSocketConnection';
import { useImageHandling } from './hooks/useImageHandling';
import { useBoxManagement } from './hooks/useBoxManagement';
import './styles/template-training.scss';
import WebSocketService from '../../services/websocket';
import ReactDOM from 'react-dom/client';

function TemplateTraining() {
  const [agentName, setAgentName] = useState('OpenFoam');
  const [pageName, setPageName] = useState('default');
  const [inputValue, setInputValue] = useState('');

  // Custom hooks
  const { 
    isAnalyzing, 
    setIsAnalyzing, 
    detections, 
    setDetections 
  } = useSocketConnection();

  const {
    image,
    setImage,
    imageSize,
    setImageSize,
    handleImageUpload,
    handleImageLoad
  } = useImageHandling();

  const {
    boxes,
    setBoxes,
    selectedBox,
    setSelectedBox,
    captions,
    setCaptions,
    handleBoxClick,
    handleDragStop,
    createNewBox,
    deleteBox
  } = useBoxManagement(detections);

  // Add this effect to update input value when selecting a box
  useEffect(() => {
    if (selectedBox !== null && captions[selectedBox]) {
      setInputValue(captions[selectedBox]);
    } else if (selectedBox === null) {
      setInputValue('');
    }
  }, [selectedBox, captions]);

  const handleAnalyze = () => {
    if (!image) {
      alert('Please upload an image first');
      return;
    }

    setIsAnalyzing(true);
    WebSocketService.uploadScreenshot(image);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && selectedBox !== null) {
      setCaptions(prev => ({
        ...prev,
        [selectedBox]: inputValue
      }));
      setSelectedBox(null);
      setInputValue('');
    }
  };

  const handleSaveTemplates = () => {
    if (!image) {
      alert('No image available');
      return;
    }

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
        image: image,
        caption: caption,
        bbox: bbox,
        agent_name: agentName,
        page_name: pageName
      });
    });
  };

  return (
    <div className="template-training-container">
      <Toolbar
        agentName={agentName}
        setAgentName={setAgentName}
        pageName={pageName}
        setPageName={setPageName}
        handleImageUpload={handleImageUpload}
        handleAnalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleKeyPress={handleKeyPress}
        selectedBox={selectedBox}
        handleSaveTemplates={handleSaveTemplates}
        hasCaptions={Object.keys(captions).length > 0}
        onDeleteBox={() => selectedBox !== null && deleteBox(selectedBox)}
      />

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
    </div>
  );
}

if (document.getElementById('root')) {
  const container = document.getElementById('root');
  const root = ReactDOM.createRoot(container);
  root.render(<TemplateTraining />);
}

export default TemplateTraining; 