import { useState } from 'react';

export const useImageHandling = (cleanupFunctions = {}) => {
  const [image, setImage] = useState(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Clear all existing data if cleanupFunctions provided
      if (cleanupFunctions) {
        cleanupFunctions.setDetections?.([]);
        cleanupFunctions.setBoxes?.({});
        cleanupFunctions.setCaptions?.({});
        cleanupFunctions.setSelectedBox?.(null);
        cleanupFunctions.setIsAnalyzing?.(false);
      }

      // Clear image size
      setImageSize({ width: 0, height: 0 });
      
      // Set new image
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64Image = e.target.result;
        setImage(base64Image);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleImageLoad = (e) => {
    const img = e.target;
    setImageSize({
      width: img.naturalWidth,
      height: img.naturalHeight
    });
  };

  const getImageSrc = (imageData) => {
    if (!imageData) return '';
    if (imageData.startsWith('data:')) {
      return imageData;
    }
    return `data:image/jpeg;base64,${imageData}`;
  };

  return {
    image,
    setImage,
    imageSize,
    setImageSize,
    handleImageUpload,
    handleImageLoad,
    getImageSrc
  };
}; 