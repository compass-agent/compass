import React, { useEffect } from 'react';
import { FaSearchLocation } from 'react-icons/fa';
import { useAppState } from '../../../context/AppContext';

function CoordinatePreviewButton({ x, y }) {
  const { state } = useAppState();
  const { scaling } = state;

  useEffect(() => {
    return () => {
      window.coordinatePreview.hidePreview();
    };
  }, []);

  const handleClick = () => {
    console.log('Starting coordinate scaling...');
    // FIXME: Still the scaling is not being recevied from the backend. So it goes with the default scaling factors defined in the context.
    const scaledX = Math.round(x * scaling.xFactor);
    const scaledY = Math.round(y * scaling.yFactor);
    
    console.log('Showing preview at:', {
      original: { x, y },
      scaled: { x: scaledX, y: scaledY },
      factors: scaling
    });

    window.coordinatePreview.showPreview(scaledX, scaledY);
    setTimeout(() => {
      window.coordinatePreview.hidePreview();
    }, 2000);
  };

  return (
    <button 
      className="coordinate-preview-button"
      onClick={handleClick}
      title={`Preview coordinate (${x}, ${y})`}
    >
      <FaSearchLocation />
    </button>
  );
}

export default CoordinatePreviewButton; 