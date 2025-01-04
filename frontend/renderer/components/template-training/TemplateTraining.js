import React, { useState, useEffect } from 'react';
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

    newSocket.on('template_saved', (response) => {
      console.log('Template saved successfully:', response);
      // Optionally show success message to user
    });

    newSocket.on('template_save_error', (error) => {
      console.error('Error saving template:', error);
      alert('Error saving template: ' + error.message);
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

  // Add this new effect to handle keyboard events
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if (!selectedBox) return;

      const MOVE_AMOUNT = 1; // pixels to move/resize per keypress
      const box = boxes[selectedBox] || {
        x: detections[selectedBox]?.bbox[0] || 0,
        y: detections[selectedBox]?.bbox[1] || 0,
        width: (detections[selectedBox]?.bbox[2] - detections[selectedBox]?.bbox[0]) || 0,
        height: (detections[selectedBox]?.bbox[3] - detections[selectedBox]?.bbox[1]) || 0
      };

      if (e.shiftKey) {
        // Move box with Shift + Arrow keys
        switch (e.key) {
          case 'ArrowLeft': 
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, x: box.x - MOVE_AMOUNT }}));
            break;
          case 'ArrowRight':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, x: box.x + MOVE_AMOUNT }}));
            break;
          case 'ArrowUp':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, y: box.y - MOVE_AMOUNT }}));
            break;
          case 'ArrowDown':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, y: box.y + MOVE_AMOUNT }}));
            break;
        }
      } else if (e.metaKey) {
        // Prevent default browser behavior for Cmd + Arrow keys
        e.preventDefault();
        
        // Resize box with Command + Arrow keys
        switch (e.key) {
          case 'ArrowLeft':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, width: box.width - MOVE_AMOUNT }}));
            break;
          case 'ArrowRight':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, width: box.width + MOVE_AMOUNT }}));
            break;
          case 'ArrowUp':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, height: box.height - MOVE_AMOUNT }}));
            break;
          case 'ArrowDown':
            setBoxes(prev => ({ ...prev, [selectedBox]: { ...box, height: box.height + MOVE_AMOUNT }}));
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedBox, boxes, detections]);

  // Add this effect to initialize boxes when detections change
  useEffect(() => {
    if (detections && detections.length > 0) {
      const initialBoxes = {};
      detections.forEach((detection, index) => {
        initialBoxes[index] = {
          x: detection.bbox[0],
          y: detection.bbox[1],
          width: detection.bbox[2] - detection.bbox[0],
          height: detection.bbox[3] - detection.bbox[1]
        };
      });
      setBoxes(initialBoxes);
    }
  }, [detections]);

  // Add this effect to update imageSize when image loads
  useEffect(() => {
    const imageElement = document.querySelector('.image-container img');
    if (imageElement) {
      const updateImageSize = () => {
        setImageSize({
          width: imageElement.naturalWidth,
          height: imageElement.naturalHeight
        });
      };
      imageElement.addEventListener('load', updateImageSize);
      // In case image is already loaded
      if (imageElement.complete) {
        updateImageSize();
      }
      return () => imageElement.removeEventListener('load', updateImageSize);
    }
  }, []);

  // Add this useEffect to debug
  useEffect(() => {
    console.log('Detections:', detections);
    console.log('Boxes:', boxes);
    console.log('ImageSize:', imageSize);
  }, [detections, boxes, imageSize]);

  // Initialize boxes when detections change
  useEffect(() => {
    if (!detections) return;
    
    const initialBoxes = {};
    detections.forEach((detection, index) => {
      if (detection && detection.bbox) {
        initialBoxes[index] = {
          x: detection.bbox[0] || 0,
          y: detection.bbox[1] || 0,
          width: (detection.bbox[2] - detection.bbox[0]) || 0,
          height: (detection.bbox[3] - detection.bbox[1]) || 0
        };
      }
    });
    setBoxes(initialBoxes);
  }, [detections]);

  // Image size effect
  useEffect(() => {
    const imageElement = document.querySelector('.image-container img');
    if (!imageElement) return;

    const updateImageSize = () => {
      setImageSize({
        width: imageElement.naturalWidth || imageElement.offsetWidth,
        height: imageElement.naturalHeight || imageElement.offsetHeight
      });
    };

    imageElement.addEventListener('load', updateImageSize);
    if (imageElement.complete) {
      updateImageSize();
    }

    return () => imageElement.removeEventListener('load', updateImageSize);
  }, []);

  // Render boxes
  const renderBoxes = () => {
    if (!detections || !Array.isArray(detections)) return null;

    return detections.map((detection, index) => {
      if (!detection || !detection.bbox) return null;

      const imageElement = document.querySelector('.image-container img');
      if (!imageElement) return null;

      const displayedWidth = imageElement.offsetWidth || 1;
      const displayedHeight = imageElement.offsetHeight || 1;

      const scaleX = displayedWidth / (imageSize.width || 1);
      const scaleY = displayedHeight / (imageSize.height || 1);

      const box = boxes[index] || {
        x: detection.bbox[0] || 0,
        y: detection.bbox[1] || 0,
        width: (detection.bbox[2] - detection.bbox[0]) || 0,
        height: (detection.bbox[3] - detection.bbox[1]) || 0
      };

      const scaledBox = {
        x: Math.round(box.x * scaleX),
        y: Math.round(box.y * scaleY),
        width: Math.round(box.width * scaleX),
        height: Math.round(box.height * scaleY)
      };

      return (
        <div
          key={index}
          className={`detection-box ${selectedBox === index ? 'selected' : ''} ${captions?.[index] ? 'labeled' : ''}`}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: `${scaledBox.width}px`,
            height: `${scaledBox.height}px`,
            border: selectedBox === index ? '2px solid #ff0000' : 
                   captions?.[index] ? '2px solid #0088ff' : 
                   '2px solid #00ff00',
            cursor: 'pointer',
            backgroundColor: 'rgba(0, 255, 0, 0.1)',
            transform: `translate(${scaledBox.x}px, ${scaledBox.y}px)`
          }}
          onClick={(e) => {
            e.stopPropagation();
            if (typeof handleBoxClick === 'function') {
              handleBoxClick(index);
            }
          }}
        />
      );
    });
  };

  const handleSaveTemplates = () => {
    if (!socket || !image) {
      alert('No connection or image available');
      return;
    }

    // Save each captioned box as a template
    Object.entries(captions).forEach(([boxIndex, caption]) => {
      const box = boxes[boxIndex];
      if (!box) return;

      // Convert box coordinates back to original format [x1, y1, x2, y2]
      const bbox = [
        box.x,
        box.y,
        box.x + box.width,
        box.y + box.height
      ];

      socket.emit('save_template', {
        image: image,
        caption: caption,
        bbox: bbox
      });
    });
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
          onClick={handleSaveTemplates}
          disabled={Object.keys(captions).length === 0}
        >
          <FontAwesomeIcon icon={faSave} /> Save All Templates
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
            {renderBoxes()}
          </div>
        )}
      </div>
    </div>
  );
}

export default TemplateTraining; 