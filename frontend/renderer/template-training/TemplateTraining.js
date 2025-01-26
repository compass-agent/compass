import React, { useState, useEffect } from 'react';
import AgentSetup from './components/AgentSetup';
import PagesList from './components/PagesList';
import PageEditor from './components/PageEditor';
import NavigationBar from './components/NavigationBar';
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

  const handleAnalyze = () => {
    if (!image) {
      alert('Please upload an image first');
      return;
    }
    setIsAnalyzing(true);
    
    // Remove the data URL prefix if it exists
    const base64Image = image.split(',')[1] || image;
    
    WebSocketService.uploadScreenshot(base64Image, agentData.name);
  };

  const handleSaveTemplates = () => {
    if (!image || Object.keys(captions).length === 0) {
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
        image: image,
        caption: caption,
        bbox: bbox,
        agent_name: agentData.name,
        page_name: 'default' // You might want to make this configurable
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
            pages={agentData.pages}
            onAddPage={() => setCurrentView(VIEW_STATES.PAGE_EDITOR)}
            onEditPage={(pageIndex) => {
              // Handle edit page
            }}
          />
        );
      case VIEW_STATES.PAGE_EDITOR:
        // Convert boxes object to array
        const boxesArray = Object.entries(boxes).map(([index, box]) => ({
          ...box,
          id: index,
          caption: captions[index]
        }));

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
            image={image}
            setImage={setImage}
            boxes={boxesArray}
            selectedBox={selectedBox}
            handleBoxClick={handleBoxClick}
            createNewBox={createNewBox}
            deleteBox={deleteBox}
            inputValue={inputValue}
            setInputValue={setInputValue}
            handleKeyPress={handleKeyPress}
            captions={captions}
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
      <NavigationBar 
        currentView={currentView}
        agentName={agentData.name}
      />
      <div className="content">
        {renderCurrentView()}
      </div>
    </div>
  );
};

export default TemplateTraining; 