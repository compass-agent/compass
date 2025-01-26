import React from 'react';
import '../styles/components/DetectionBox.scss';

const DetectionBox = ({
  index,
  box,
  scaledBox,
  isSelected,
  hasCaption,
  onClick
}) => {
  return (
    <div
      className={`detection-box ${isSelected ? 'selected' : ''} ${hasCaption ? 'labeled' : ''}`}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: `${scaledBox.width}px`,
        height: `${scaledBox.height}px`,
        border: isSelected ? '2px solid #ff0000' : 
               hasCaption ? '2px solid #0088ff' : 
               '2px solid #00ff00',
        backgroundColor: 'rgba(0, 255, 0, 0.1)',
        transform: `translate(${scaledBox.x}px, ${scaledBox.y}px)`
      }}
      onClick={(e) => {
        e.stopPropagation();
        onClick(index);
      }}
    />
  );
};

export default DetectionBox; 