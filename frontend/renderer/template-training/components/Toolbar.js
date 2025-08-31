import {
  faObjectGroup,
  faSave,
  faTimes,
  faTrash,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React from "react"
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
  return (
    <div className="toolbar">
      {/* Action Buttons Row */}
      <div className="toolbar-actions">
        <div className="left-actions">
          <button
            onClick={handleAnalyze}
            className="extract-button"
            disabled={isAnalyzing}
          >
            <FontAwesomeIcon icon={faObjectGroup} />
            {isAnalyzing ? "Extracting Templates..." : "Extract Templates"}
          </button>
        </div>

        <div className="right-actions">
          <button onClick={onCancel} className="cancel-button">
            <FontAwesomeIcon icon={faTimes} /> Cancel
          </button>
          <button onClick={handleSaveTemplates} className="save-button">
            <FontAwesomeIcon icon={faSave} /> Save
          </button>
        </div>
      </div>

      {/* Caption Input Row */}
      <div className="toolbar-input">
        <div className="input-section">
          <label className="input-label">
            {selectedBox !== null
              ? "Edit Template Caption"
              : "Select a template to add caption"}
          </label>
          <div className="input-row">
            <textarea
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
            {selectedBox !== null && (
              <button
                onClick={onDeleteBox}
                className="delete-button"
                title="Delete selected template"
              >
                <FontAwesomeIcon icon={faTrash} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Toolbar
