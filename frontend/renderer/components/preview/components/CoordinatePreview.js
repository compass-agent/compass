import React from 'react';
import '../../../styles/preview/CoordinatePreview.scss';

function CoordinatePreview({ x, y, visible }) {
  console.log('CoordinatePreview render:', { x, y, visible });

  if (!visible) {
    console.log('Preview not visible, returning null');
    return null;
  }

  console.log('Rendering preview at coordinates:', x, y);
  return (
    <div 
      className="coordinate-preview"
      style={{
        position: 'fixed',
        left: `${x}px`,
        top: `${y}px`,
        pointerEvents: 'none',  // This ensures the preview doesn't interfere with other interactions
        zIndex: 9999  // Ensure it's on top of other elements
      }}
    />
  );
}

export default CoordinatePreview; 