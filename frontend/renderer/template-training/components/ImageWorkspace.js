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
    if (!detections || !Array.isArray(detections)) return null;

    return detections.map((detection, index) => {
      if (!boxes[index]) return null;

      if (!detection || !detection.bbox) return null;

      const imageElement = document.querySelector('.image-container img');
      if (!imageElement) return null;

      const displayedWidth = imageElement.offsetWidth || 1;
      const displayedHeight = imageElement.offsetHeight || 1;

      const scaleX = displayedWidth / (imageSize.width || 1);
      const scaleY = displayedHeight / (imageSize.height || 1);

      const box = boxes[index];
      const scaledBox = {
        x: Math.round(box.x * scaleX),
        y: Math.round(box.y * scaleY),
        width: Math.round(box.width * scaleX),
        height: Math.round(box.height * scaleY)
      };

      return (
        <DetectionBox
          key={index}
          index={index}
          box={box}
          scaledBox={scaledBox}
          isSelected={selectedBox === index}
          hasCaption={!!captions[index]}
          onClick={handleBoxClick}
        />
      );
    });
  };

  const handleWorkspaceClick = (e) => {
    if (e.altKey) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      createNewBox(x, y);
    }
  };

  return (
    <div className="image-workspace">
      {image && (
        <div 
          className="image-container"
          onClick={handleWorkspaceClick}
        >
          <img 
            src={`data:image/png;base64,${image}`}
            alt="Template"
            onLoad={handleImageLoad}
          />
          {renderBoxes()}
        </div>
      )}
    </div>
  );
};

export default ImageWorkspace; 