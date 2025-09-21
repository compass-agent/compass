import {
  faObjectGroup,
  faSave,
  faTimes,
  faPaperPlane,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useRef } from "react"
import "../styles/components/Toolbar.scss"

const Toolbar = ({
  handleAnalyze,
  handleSaveTemplates,
  isAnalyzing,
  inputValue,
  setInputValue,
  handleKeyPress,
  selectedBox,
  onDeleteBox,
  onCancel,
  pageName,
  agentName,
}) => {
  const inputRef = useRef(null);

  // Auto-focus input when a template is selected
  useEffect(() => {
    if (selectedBox !== null && inputRef.current) {
      inputRef.current.focus();
    }
  }, [selectedBox]);

  const handleSubmit = () => {
    if (selectedBox !== null && inputValue.trim()) {
      // Simulate Enter key press
      const enterEvent = {
        key: "Enter",
        preventDefault: () => {}
      };
      handleKeyPress(enterEvent);
    }
  };

  return (
    <div className="toolbar">
      {/* Action Buttons and Caption Input Row */}
      <div className="toolbar-main">
        <div className="left-section">
          <button
            onClick={handleAnalyze}
            className="extract-button"
            disabled={isAnalyzing}
          >
            <FontAwesomeIcon icon={faObjectGroup} />
            {isAnalyzing ? "Extracting Templates..." : "Extract Templates"}
          </button>
          
          <div className="caption-section">
            <label className="input-label">
              {selectedBox !== null
                ? "Edit Template Caption"
                : "Select a template to add caption"}
            </label>
            <div className="input-row">
              <textarea
                ref={inputRef}
                placeholder={
                  selectedBox !== null
                    ? "Enter caption for the selected template..."
                    : "Select a template first"
                }
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={selectedBox === null}
                rows={2}
                className="caption-input"
              />
              {selectedBox !== null && inputValue.trim() && (
                <button
                  onClick={handleSubmit}
                  className="submit-button"
                  title="Submit caption (same as pressing Enter)"
                >
                  <FontAwesomeIcon icon={faPaperPlane} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Actions Row */}
      <div className="toolbar-bottom-actions">
        <button onClick={onCancel} className="cancel-button">
          <FontAwesomeIcon icon={faTimes} /> Cancel
        </button>
        <button onClick={handleSaveTemplates} className="save-button">
          <FontAwesomeIcon icon={faSave} /> Save
        </button>
      </div>
    </div>
  )
}

export default Toolbar
