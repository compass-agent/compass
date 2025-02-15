import React from 'react';
import '../styles/components/ContextMenu.scss';

const ContextMenu = ({ x, y, onClose, options }) => {
  return (
    <>
      <div className="context-menu-overlay" onClick={onClose} />
      <div 
        className="context-menu" 
        style={{ 
          left: `${x}px`, 
          top: `${y}px` 
        }}
      >
        {options.map((option, index) => (
          <button
            key={index}
            className={`menu-item ${option.disabled ? 'disabled' : ''}`}
            onClick={() => {
              if (!option.disabled) {
                option.onClick();
                onClose();
              }
            }}
            disabled={option.disabled}
          >
            {option.label}
          </button>
        ))}
      </div>
    </>
  );
};

export default ContextMenu; 