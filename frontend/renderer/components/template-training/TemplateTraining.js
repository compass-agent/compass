import React, { useState } from 'react';
import Draggable from 'react-draggable';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload, faSearch, faSave } from '@fortawesome/free-solid-svg-icons';
import io from 'socket.io-client';
import '../../styles/template-training.scss';

function TemplateTraining() {
  const [image, setImage] = useState(null);
  const [templateName, setTemplateName] = useState('');
  const [detections, setDetections] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [socket, setSocket] = useState(null);
  const [selectedBox, setSelectedBox] = useState(null);
  const [captions, setCaptions] = useState({});
  const [inputValue, setInputValue] = useState('');
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [boxes, setBoxes] = useState({});

  // Initialize socket connection
  React.useEffect(() => {
    const newSocket = io('http://localhost:5001');
    
    newSocket.on('connect', () => {
      console.log('Connected to server');
    });

    newSocket.on('detection_result', (result) => {
      console.log('Received detection results:', result);
      setDetections(result.detections);
      setIsAnalyzing(false);
    });

    newSocket.on('error', (error) => {
      console.error('Server error:', error);
      setIsAnalyzing(false);
      alert('Error analyzing image: ' + error.message);
    });

    setSocket(newSocket);

    return () => newSocket.disconnect();
  }, []);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64Image = e.target.result.split(',')[1]; // Remove data URL prefix
        setImage(base64Image);
        setDetections([]); // Clear previous detections
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = () => {
    if (!image || !socket) {
      alert('Please upload an image first');
      return;
    }

    setIsAnalyzing(true);
    socket.emit('upload_screenshot', { image });
  };

  const handleImageLoad = (e) => {
    const img = e.target;
    console.log('Image loaded:', {
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      offsetWidth: img.offsetWidth,
      offsetHeight: img.offsetHeight
    });
    setImageSize({
      width: img.naturalWidth,
      height: img.naturalHeight
    });
  };

  const handleBoxClick = (index) => {
    setSelectedBox(index);
    setInputValue(captions[index] || '');
    document.querySelector('input[placeholder="Enter caption for selected box"]').focus();
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

  const handleDragStop = (index, e, data) => {
    setBoxes(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        x: data.x,
        y: data.y
      }
    }));
  };

  return (
    <div className="template-training-container">
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
          disabled={!image || isAnalyzing}
        >
          <FontAwesomeIcon icon={faSearch} /> 
          {isAnalyzing ? 'Analyzing...' : 'Analyze'}
        </button>
        <input
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
          onClick={() => {/* Save to backend implementation */}}
          disabled={Object.keys(captions).length === 0}
        >
          Save All Templates
        </button>
      </div>

      <div className="image-workspace">
        {image && (
          <div className="image-container">
            <img 
              src={`data:image/png;base64,${image}`}
              alt="Template"
              onLoad={handleImageLoad}
            />
            {detections.map((detection, index) => {
              const imageElement = document.querySelector('.image-container img');
              const displayedWidth = imageElement ? imageElement.offsetWidth : 0;
              const displayedHeight = imageElement ? imageElement.offsetHeight : 0;

              const scaleX = displayedWidth / imageSize.width;
              const scaleY = displayedHeight / imageSize.height;

              const x = Math.round(detection.bbox[0] * scaleX);
              const y = Math.round(detection.bbox[1] * scaleY);
              const width = Math.round((detection.bbox[2] - detection.bbox[0]) * scaleX);
              const height = Math.round((detection.bbox[3] - detection.bbox[1]) * scaleY);

              return (
                <Draggable
                  key={index}
                  defaultPosition={{x, y}}
                  position={boxes[index] ? boxes[index] : null}
                  onStop={(e, data) => handleDragStop(index, e, data)}
                  bounds="parent"
                >
                  <div
                    className={`detection-box ${selectedBox === index ? 'selected' : ''} ${captions[index] ? 'labeled' : ''}`}
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      width: `${width}px`,
                      height: `${height}px`,
                      border: selectedBox === index ? '2px solid #ff0000' : 
                             captions[index] ? '2px solid #0088ff' : 
                             '2px solid #00ff00',
                      cursor: 'move',
                      backgroundColor: 'rgba(0, 255, 0, 0.1)',
                      transform: `translate(${x}px, ${y}px)`
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleBoxClick(index);
                    }}
                  >
                    {captions[index] && (
                      <div className="caption-label">
                        {captions[index]}
                      </div>
                    )}
                  </div>
                </Draggable>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default TemplateTraining; 