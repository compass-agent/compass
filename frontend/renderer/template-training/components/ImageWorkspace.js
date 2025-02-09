import React, { useRef, useState, useEffect } from 'react';
import ContextMenu from './ContextMenu';
import '../styles/components/ImageWorkspace.scss';

const ImageWorkspace = ({
  image,
  handleImageLoad,
  imageSize,
  boxes,
  selectedBox,
  captions,
  handleBoxClick,
  createNewBox,
  deleteBox,
  getImageSrc,
  handleAutoCaption
}) => {
  const [contextMenu, setContextMenu] = useState(null);
  const imageRef = useRef(null);
  const containerRef = useRef(null);

  const getImagePosition = () => {
    const imageElement = imageRef.current;
    const containerElement = containerRef.current;
    if (!imageElement || !containerElement) {
      console.log('Missing refs:', { imageRef: !!imageElement, containerRef: !!containerElement });
      return { offsetX: 0, offsetY: 0 };
    }

    const containerRect = containerElement.getBoundingClientRect();
    const imageRect = imageElement.getBoundingClientRect();

    const position = {
      offsetX: imageRect.left - containerRect.left,
      offsetY: imageRect.top - containerRect.top
    };
    
    console.log('Image position:', position);
    return position;
  };

  const getScalingFactors = () => {
    const imageElement = imageRef.current;
    if (!imageElement) {
      console.log('Missing imageRef in getScalingFactors');
      return { scaleX: 1, scaleY: 1 };
    }

    const displayedWidth = imageElement.offsetWidth;
    const displayedHeight = imageElement.offsetHeight;
    const originalWidth = imageSize.width || imageElement.naturalWidth;
    const originalHeight = imageSize.height || imageElement.naturalHeight;

    const factors = {
      scaleX: displayedWidth / originalWidth,
      scaleY: displayedHeight / originalHeight
    };
    return factors;
  };

  const handleContextMenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Context menu triggered', { x: e.clientX, y: e.clientY });
    
    // Close any existing context menu first
    if (contextMenu) {
      handleCloseContextMenu();
    }

    // Get the clicked box element
    const boxElement = e.target.closest('.detection-box');
    const boxId = boxElement ? boxElement.dataset.boxId : null;

    console.log('Context menu event:', {
      target: e.target,
      boxElement,
      boxId,
      boxes: {...boxes}
    });

    const menuOptions = boxId !== null ? [
      {
        label: 'Delete Box',
        onClick: () => {
          console.log('Deleting box with ID:', boxId);
          deleteBox(boxId);
        }
      },
      {
        label: 'Auto Caption',
        onClick: () => handleAutoCaption(boxId),
        disabled: !!captions[boxId]
      }
    ] : [
      {
        label: 'Add Box',
        onClick: () => {
          const imageElement = imageRef.current;
          const rect = imageElement.getBoundingClientRect();
          const { scaleX, scaleY } = getScalingFactors();
          const x = (e.clientX - rect.left) / scaleX;
          const y = (e.clientY - rect.top) / scaleY;
          console.log('Creating new box at:', { x, y });
          createNewBox(x, y);
        }
      }
    ];

    setTimeout(() => {
      setContextMenu({
        x: e.clientX,
        y: e.clientY,
        options: menuOptions,
        boxId
      });
    }, 0);
  };

  const handleCloseContextMenu = () => {
    console.log('Closing context menu:', contextMenu);
    setContextMenu(null);
  };

  useEffect(() => {
    const handleClick = (e) => {
      if (contextMenu && !e.target.closest('.context-menu')) {
        console.log('Click outside context menu');
        handleCloseContextMenu();
      }
    };

    const handleGlobalContextMenu = (e) => {
      // Only handle context menu events outside the image-workspace
      if (!e.target.closest('.image-workspace')) {
        console.log('Context menu outside image workspace');
        handleCloseContextMenu();
      }
    };

    document.addEventListener('click', handleClick);
    document.addEventListener('contextmenu', handleGlobalContextMenu);
    
    return () => {
      document.removeEventListener('click', handleClick);
      document.removeEventListener('contextmenu', handleGlobalContextMenu);
    };
  }, [contextMenu]);

  useEffect(() => {
    console.log('Number of boxes:', Object.keys(boxes).length);
  }, [boxes]);

  const renderBoxes = () => {
    console.log('Rendering boxes:', boxes);
    const { scaleX, scaleY } = getScalingFactors();
    const { offsetX, offsetY } = getImagePosition();

    return Object.entries(boxes).map(([id, box]) => {
      const scaledBox = {
        x: Math.round(box.x * scaleX) + offsetX,
        y: Math.round(box.y * scaleY) + offsetY,
        width: Math.round(box.width * scaleX),
        height: Math.round(box.height * scaleY)
      };

      return (
        <div
          key={id}
          data-box-id={id}
          className={`detection-box ${selectedBox === id ? 'selected' : ''} ${captions[id] ? 'labeled' : ''}`}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: `${scaledBox.width}px`,
            height: `${scaledBox.height}px`,
            transform: `translate(${scaledBox.x}px, ${scaledBox.y}px)`
          }}
          onClick={(e) => {
            e.stopPropagation();
            handleBoxClick(id);
          }}
          onContextMenu={(e) => {
            e.stopPropagation();
            handleContextMenu(e);
          }}
        >
          {captions[id] && (
            <div className="caption-preview">
              {captions[id]}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="image-workspace">
      <div 
        className="image-container" 
        ref={containerRef}
        onContextMenu={handleContextMenu}
      >
        <img
          ref={imageRef}
          src={getImageSrc(image)}
          alt="Workspace"
          onLoad={(e) => {
            console.log('Image loaded:', {
              width: e.target.width,
              height: e.target.height,
              naturalWidth: e.target.naturalWidth,
              naturalHeight: e.target.naturalHeight
            });
            handleImageLoad(e);
          }}
        />
        {renderBoxes()}
      </div>

      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          options={contextMenu.options}
          onClose={handleCloseContextMenu}
        />
      )}
    </div>
  );
};

export default ImageWorkspace; 