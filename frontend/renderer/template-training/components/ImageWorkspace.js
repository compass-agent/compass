import React from 'react';
import DetectionBox from './DetectionBox';
import '../styles/components/ImageWorkspace.scss';

const ImageWorkspace = ({
  image,
  handleImageLoad,
  detections,
  boxes,
  imageSize,
  selectedBox,
  captions,
  handleBoxClick,
  createNewBox
}) => {
  const renderBoxes = () => {
    console.log('renderBoxes called with:', {
      detections,
      boxes,
      imageSize,
      selectedBox,
      captions
    });

    if (!boxes || (!Array.isArray(boxes) && Object.keys(boxes).length === 0)) {
      console.log('No boxes to render');
      return null;
    }

    const imageElement = document.querySelector('.image-container img');
    if (!imageElement) {
      console.log('No image element found');
      return null;
    }

    const displayedWidth = imageElement.offsetWidth;
    const displayedHeight = imageElement.offsetHeight;
    const originalWidth = imageSize?.width || imageElement.naturalWidth;
    const originalHeight = imageSize?.height || imageElement.naturalHeight;

    console.log('Image dimensions:', {
      displayedWidth,
      displayedHeight,
      originalWidth,
      originalHeight
    });

    const scaleX = displayedWidth / originalWidth;
    const scaleY = displayedHeight / originalHeight;

    console.log('Scale factors:', { scaleX, scaleY });

    // Handle both array and object formats
    const boxesArray = Array.isArray(boxes) ? boxes : Object.entries(boxes).map(([id, box]) => ({
      ...box,
      id
    }));

    return boxesArray.map((box, index) => {
      const scaledBox = {
        x: box.x * scaleX,
        y: box.y * scaleY,
        width: box.width * scaleX,
        height: box.height * scaleY
      };

      console.log(`Box ${index}:`, {
        original: box,
        scaled: scaledBox,
        isSelected: selectedBox === index,
        hasCaption: captions && captions[index]
      });

      return (
        <DetectionBox
          key={box.id || index}
          index={box.id || index}
          box={box}
          scaledBox={scaledBox}
          isSelected={selectedBox === box.id || selectedBox === index}
          hasCaption={box.caption || (captions && captions[index])}
          onClick={handleBoxClick}
        />
      );
    });
  };

  const handleImageClick = (e) => {
    if (!imageSize?.width || !imageSize?.height) return;

    const rect = e.target.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    createNewBox(x, y);
  };

  console.log('ImageWorkspace render:', { image, boxes });

  return (
    <div className="image-workspace">
      {image && (
        <div className="image-container" onClick={handleImageClick}>
          <img
            src={getImageSrc(image)}
            alt="Template"
            onLoad={(e) => {
              console.log('Image loaded:', e.target.naturalWidth, e.target.naturalHeight);
              handleImageLoad(e);
            }}
          />
          {renderBoxes()}
        </div>
      )}
    </div>
  );
};

// Helper function to handle image source
const getImageSrc = (imageData) => {
  if (!imageData) return '';
  if (imageData.startsWith('data:')) {
    return imageData;
  }
  return `data:image/jpeg;base64,${imageData}`;
};

export default ImageWorkspace; 