import React, { useEffect } from 'react';

function CoordinatePreviewButton({ x, y }) {
  useEffect(() => {
    return () => {
      // Cleanup on unmount
      window.coordinatePreview.hidePreview();
    };
  }, []);

  const handleClick = () => {
    console.log('Showing preview at:', x, y);
    window.coordinatePreview.showPreview(x, y);
    setTimeout(() => {
      window.coordinatePreview.hidePreview();
    }, 2000);
  };

  return (
    <button 
      className="coordinate-preview-button"
      onClick={handleClick}
    >
      highlight
    </button>
  );
}

export default CoordinatePreviewButton; 