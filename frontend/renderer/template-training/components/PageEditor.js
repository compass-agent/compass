import { faCamera, faUpload } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useState } from "react"
import WebSocketService from "../../common/services/websocket"
import { VIEW_STATES } from "../constants/viewStates"
import { useImageHandling } from "../hooks/useImageHandling"
import "../styles/components/PageEditor.scss"
import ImageWorkspace from "./ImageWorkspace"
import SaveDialog from "./SaveDialog"
import Toolbar from "./Toolbar"

const PageEditor = ({
  handleAnalyze,
  isAnalyzing,
  boxes,
  selectedBox,
  handleBoxClick,
  createNewBox,
  deleteBox,
  inputValue,
  setInputValue,
  handleKeyPress,
  captions,
  setCurrentView,
  setDetections,
  setBoxes,
  setCaptions,
  setSelectedBox,
  setIsAnalyzing,
  currentScreenshot,
  agentName,
  handleAutoCaption,
  pageName: parentPageName,
  setPageName: setParentPageName,
}) => {
  const [pageName, setPageName] = useState("")
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false)

  const cleanupFunctions = {
    setDetections,
    setBoxes,
    setCaptions,
    setSelectedBox,
    setIsAnalyzing,
  }

  const {
    image,
    setImage,
    imageSize,
    handleImageLoad,
    handleImageUpload,
    getImageSrc,
  } = useImageHandling(cleanupFunctions)

  useEffect(() => {
    if (currentScreenshot) {
      setImage(currentScreenshot.image)
      // Backend returns screenshot with 'name' property
      const name = currentScreenshot.name || ""
      setPageName(name)
      if (setParentPageName) {
        setParentPageName(name)
      }
    } else {
      setPageName("")
      if (setParentPageName) {
        setParentPageName("")
      }
    }
  }, [currentScreenshot, setParentPageName])

  useEffect(() => {
    console.log("Number of boxes:", Object.keys(boxes).length)
  }, [boxes])

  useEffect(() => {
    const handleDetectionResult = (data) => {
      console.log("Handling detection result:", data)
      if (data.detections) {
        setDetections(data.detections)
        setIsAnalyzing(false)
      }
    }

    WebSocketService.stateHandlers.onDetectionResult = handleDetectionResult

    return () => {
      WebSocketService.stateHandlers.onDetectionResult = null
    }
  }, [setDetections, setIsAnalyzing])

  const handleSave = () => {
    if (!image) {
      alert("No image available")
      return
    }

    if (Object.keys(captions).length === 0) {
      alert("No templates to save")
      return
    }

    setIsSaveDialogOpen(true)
  }

  const handleFinalSave = (newPageName) => {
    const imageData = image.includes("base64,")
      ? image.split("base64,")[1]
      : image

    const templates = Object.entries(captions)
      .map(([boxIndex, caption]) => {
        const box = boxes[boxIndex]
        if (!box) return null

        return {
          id: box.id,
          bbox: [box.x, box.y, box.x + box.width, box.y + box.height],
          caption: caption,
        }
      })
      .filter((template) => template !== null)

    // Add a success handler for saveTemplates
    WebSocketService.stateHandlers.onTemplatesSaved = (data) => {
      setIsSaveDialogOpen(false)

      if (data.success) {
        // Trigger a refresh of screenshots before changing view
        WebSocketService.getScreenshots(agentName)

        // Navigate back to pages list - this will also clear currentScreenshot
        setCurrentView(VIEW_STATES.PAGES_LIST)
      } else {
        alert(`Error saving templates: ${data.message}`)
      }
    }

    WebSocketService.saveTemplates({
      image: imageData,
      agent_name: agentName,
      page_name: newPageName.trim(),
      templates: templates,
    })
  }

  const handleBoxChange = (boxId, newBox) => {
    setBoxes((prev) => ({
      ...prev,
      [boxId]: newBox,
    }))
  }

  return (
    <div className="page-editor">
      <Toolbar
        handleAnalyze={() => handleAnalyze(image)}
        handleSaveTemplates={handleSave}
        isAnalyzing={isAnalyzing}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleKeyPress={handleKeyPress}
        selectedBox={selectedBox}
        onDeleteBox={() => deleteBox(selectedBox)}
        onCancel={() => setCurrentView(VIEW_STATES.PAGES_LIST)}
        pageName={pageName}
        setPageName={setPageName}
        agentName={agentName}
      />

      <SaveDialog
        isOpen={isSaveDialogOpen}
        onClose={() => setIsSaveDialogOpen(false)}
        onSave={handleFinalSave}
        initialPageName={pageName}
        isExisting={!!currentScreenshot}
      />

      <div className="editor-content">
        {!image && !currentScreenshot ? (
          <div className="upload-area">
            <div className="upload-buttons">
              <input
                type="file"
                id="imageUpload"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: "none" }}
              />
              <label htmlFor="imageUpload" className="upload-button">
                <FontAwesomeIcon icon={faUpload} /> Upload Image
              </label>
              <button className="upload-button" onClick={() => {}} disabled>
                <FontAwesomeIcon icon={faCamera} /> Take Screenshot
              </button>
            </div>
            <div className="upload-instructions">
              Upload an image or take a screenshot to begin
            </div>
          </div>
        ) : (
          <ImageWorkspace
            image={image}
            handleImageLoad={handleImageLoad}
            imageSize={imageSize}
            boxes={boxes}
            selectedBox={selectedBox}
            captions={captions}
            handleBoxClick={handleBoxClick}
            createNewBox={createNewBox}
            deleteBox={deleteBox}
            getImageSrc={getImageSrc}
            handleAutoCaption={handleAutoCaption}
            onBoxChange={handleBoxChange}
          />
        )}
      </div>
    </div>
  )
}
export default PageEditor
