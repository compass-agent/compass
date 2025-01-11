import { useState, useEffect } from 'react';

export const useBoxManagement = (detections) => {
  const [boxes, setBoxes] = useState({});
  const [selectedBox, setSelectedBox] = useState(null);
  const [captions, setCaptions] = useState({});
  const [editingCaptionId, setEditingCaptionId] = useState(null);
  const [defaultIcon, setDefaultIcon] = useState(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!detections || !Array.isArray(detections)) {
      console.warn('Invalid detections data:', detections);
      return;
    }
    
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

  const handleBoxClick = (index) => {
    setSelectedBox(index);
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

  const handleIconClick = (iconId) => {
    if (selectedBox !== null) {
      setBoxes(prev => ({
        ...prev,
        [selectedBox]: {
          ...prev[selectedBox],
          icon: iconId
        }
      }));
      setEditingCaptionId(selectedBox);
    } else {
      setDefaultIcon(iconId);
    }
  };

  const updateImageSize = (width, height) => {
    setImageSize({ width, height });
  };

  const createNewBox = (x, y) => {
    const defaultWidth = 100;
    const defaultHeight = 100;

    const imageElement = document.querySelector('.image-container img');
    if (!imageElement) return;

    const displayedWidth = imageElement.offsetWidth;
    const displayedHeight = imageElement.offsetHeight;
    
    const originalWidth = imageSize.width || imageElement.naturalWidth;
    const originalHeight = imageSize.height || imageElement.naturalHeight;
    
    const scaleX = originalWidth / displayedWidth;
    const scaleY = originalHeight / displayedHeight;

    const newBox = {
      x: Math.round(x * scaleX),
      y: Math.round(y * scaleY),
      width: Math.round(defaultWidth * scaleX),
      height: Math.round(defaultHeight * scaleY)
    };

    const nextIndex = Math.max(...Object.keys(boxes).map(Number), -1) + 1;

    setBoxes(prevBoxes => ({
      ...prevBoxes,
      [nextIndex]: newBox
    }));

    setSelectedBox(nextIndex);
  };

  const deleteBox = (boxIndex) => {
    console.log('Deleting box:', boxIndex);
    
    const newBoxes = { ...boxes };
    delete newBoxes[boxIndex];
    setBoxes(newBoxes);
    
    const newCaptions = { ...captions };
    delete newCaptions[boxIndex];
    setCaptions(newCaptions);
    
    if (selectedBox === boxIndex) {
      setSelectedBox(null);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName.toLowerCase() === 'input') {
        return;
      }

      if (selectedBox === null) return;

      const STEP = e.shiftKey ? 10 : 1;

      if (e.shiftKey) {
        switch (e.key) {
          case 'ArrowLeft':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { ...prev[selectedBox], x: prev[selectedBox].x - STEP }
            }));
            e.preventDefault();
            break;
          case 'ArrowRight':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { ...prev[selectedBox], x: prev[selectedBox].x + STEP }
            }));
            e.preventDefault();
            break;
          case 'ArrowUp':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { ...prev[selectedBox], y: prev[selectedBox].y - STEP }
            }));
            e.preventDefault();
            break;
          case 'ArrowDown':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { ...prev[selectedBox], y: prev[selectedBox].y + STEP }
            }));
            e.preventDefault();
            break;
        }
      } else if (e.altKey) {
        switch (e.key) {
          case 'ArrowLeft':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { 
                ...prev[selectedBox], 
                width: Math.max(10, prev[selectedBox].width - STEP)
              }
            }));
            e.preventDefault();
            break;
          case 'ArrowRight':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { 
                ...prev[selectedBox], 
                width: prev[selectedBox].width + STEP
              }
            }));
            e.preventDefault();
            break;
          case 'ArrowUp':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { 
                ...prev[selectedBox], 
                height: Math.max(10, prev[selectedBox].height - STEP)
              }
            }));
            e.preventDefault();
            break;
          case 'ArrowDown':
            setBoxes(prev => ({
              ...prev,
              [selectedBox]: { 
                ...prev[selectedBox], 
                height: prev[selectedBox].height + STEP
              }
            }));
            e.preventDefault();
            break;
        }
      }

      if (selectedBox !== null && (e.key === 'Delete' || e.key === 'Backspace')) {
        e.preventDefault();
        deleteBox(selectedBox);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedBox]);

  return {
    boxes,
    setBoxes,
    selectedBox,
    setSelectedBox,
    captions,
    setCaptions,
    handleBoxClick,
    handleDragStop,
    handleIconClick,
    createNewBox,
    deleteBox,
    updateImageSize,
    imageSize
  };
}; 