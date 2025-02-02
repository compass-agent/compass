import React, { useState, useEffect } from 'react';
import AgentSetup from './components/AgentSetup';
import PagesList from './components/PagesList';
import PageEditor from './components/PageEditor';
import { VIEW_STATES } from './constants/viewStates';
import WebSocketService from '../common/services/websocket';
import { useSocketConnection } from './hooks/useSocketConnection';
import { useImageHandling } from './hooks/useImageHandling';
import { useBoxManagement } from './hooks/useBoxManagement';
import './styles/TemplateTraining.scss';

console.log('TemplateTraining component is rendering');

const TemplateTraining = () => {
  const [currentView, setCurrentView] = useState(VIEW_STATES.SETUP);
  const [agentData, setAgentData] = useState({
    name: '',
    pages: []
  });
  const [saveStatus, setSaveStatus] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [currentScreenshot, setCurrentScreenshot] = useState(null);

  // Custom hooks
  const { 
    isAnalyzing, 
    setIsAnalyzing, 
    detections, 
    setDetections 
  } = useSocketConnection();

  // Setup cleanup functions for image handling
  const cleanupFunctions = {
    setDetections,
    setBoxes,
    setCaptions,
    setSelectedBox,
    setIsAnalyzing
  };

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

  // Update input value when selecting a box
  useEffect(() => {
    if (selectedBox !== null && captions[selectedBox]) {
      setInputValue(captions[selectedBox]);
    } else {
      setInputValue('');
    }
  }, [selectedBox, captions]);

  // WebSocket handlers setup
  useEffect(() => {
    WebSocketService.setStateHandlers({
      ...WebSocketService.stateHandlers,
      onTemplateSaved: (data) => {
        if (data.success) {
          setSaveStatus('Templates saved successfully!');
          setTimeout(() => setSaveStatus(''), 3000);
        } else {
          setSaveStatus('Error saving templates');
        }
      }
    });
  }, []);

  const handleAnalyze = (imageData) => {
    if (!imageData) {
      alert('Please upload an image first');
      return;
    }
    setIsAnalyzing(true);
    
    const base64Image = imageData.split(',')[1] || imageData;
    WebSocketService.uploadScreenshot(base64Image, agentData.name);
  };

  const handleSaveTemplates = (imageData) => {
    if (!imageData || Object.keys(captions).length === 0) {
      alert('No templates to save');
      return;
    }

    setSaveStatus('Saving templates...');
    
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
        agent_name: agentData.name,
        page_name: 'default'
      });
    });
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

  const renderCurrentView = () => {
    switch(currentView) {
      case VIEW_STATES.SETUP:
        return (
          <AgentSetup 
            onNext={(name) => {
              setAgentData(prev => ({ ...prev, name }));
              setCurrentView(VIEW_STATES.PAGES_LIST);
            }}
          />
        );
      case VIEW_STATES.PAGES_LIST:
        return (
          <PagesList
            agentName={agentData.name}
            onAddPage={() => setCurrentView(VIEW_STATES.PAGE_EDITOR)}
            onEditPage={(screenshot) => {
              setCurrentScreenshot(screenshot);
              setCurrentView(VIEW_STATES.PAGE_EDITOR);
            }}
          />
        );
      case VIEW_STATES.PAGE_EDITOR:
        return (
          <PageEditor
            onSave={(pageData) => {
              setAgentData(prev => ({
                ...prev,
                pages: [...prev.pages, pageData]
              }));
              setCurrentView(VIEW_STATES.PAGES_LIST);
            }}
            onCancel={() => setCurrentView(VIEW_STATES.PAGES_LIST)}
            handleAnalyze={handleAnalyze}
            handleSaveTemplates={handleSaveTemplates}
            isAnalyzing={isAnalyzing}
            boxes={boxes}
            selectedBox={selectedBox}
            handleBoxClick={handleBoxClick}
            createNewBox={createNewBox}
            deleteBox={deleteBox}
            inputValue={inputValue}
            setInputValue={setInputValue}
            handleKeyPress={handleKeyPress}
            captions={captions}
            setCurrentView={setCurrentView}
            setDetections={setDetections}
            setBoxes={setBoxes}
            setCaptions={setCaptions}
            setSelectedBox={setSelectedBox}
            setIsAnalyzing={setIsAnalyzing}
            currentScreenshot={currentScreenshot}
            agentName={agentData.name}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="template-training">
      {saveStatus && (
        <div className={`save-status ${saveStatus.includes('Error') ? 'error' : 'success'}`}>
          {saveStatus}
        </div>
      )}
      <div className="content">
        {renderCurrentView()}
      </div>
    </div>
  );
};

export default TemplateTraining; 