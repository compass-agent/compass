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
  createNewBox,
  getImageSrc
}) => {
  const renderBoxes = () => {
    if (!boxes || (!Array.isArray(boxes) && Object.keys(boxes).length === 0)) {
      return null;
    }

    const imageElement = document.querySelector('.image-container img');
    if (!imageElement) {
      return null;
    }

    const displayedWidth = imageElement.offsetWidth;
    const displayedHeight = imageElement.offsetHeight;
    const originalWidth = imageSize?.width || imageElement.naturalWidth;
    const originalHeight = imageSize?.height || imageElement.naturalHeight;

    const scaleX = displayedWidth / originalWidth;
    const scaleY = displayedHeight / originalHeight;

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

  return (
    <div className="image-workspace">
      {image && (
        <div className="image-container" onClick={handleImageClick}>
          <img
            src={getImageSrc(image)}
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