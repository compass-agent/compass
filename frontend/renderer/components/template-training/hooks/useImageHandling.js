import { useState, useEffect } from 'react';

export const useImageHandling = () => {
  const [image, setImage] = useState(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64Image = e.target.result.split(',')[1];
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

  return {
    image,
    setImage,
    imageSize,
    setImageSize,
    handleImageUpload,
    handleImageLoad
  };
}; 