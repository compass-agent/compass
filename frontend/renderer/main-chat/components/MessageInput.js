import { faPlus } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useRef, useState } from "react"
import { ActionTypes, AgentStatus } from "../../common/constants"
import { useAppState } from "../../common/context/AppContext"
import WebSocketService from "../../common/services/websocket"
import "../styles/MessageInput.scss"
import InitSapConfig from "./InitSapConfig"

function MessageInput() {
  const { state, dispatch } = useAppState()
  const { connection, agent, chat } = state
  const [message, setMessage] = useState(chat.currentInput)
  const [images, setImages] = useState([])
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const isCompassReady = connection.connected //&& agent.status === AgentStatus.STOPPED
  const [tooltipPosition, setTooltipPosition] = useState({
    show: false,
    x: 0,
    y: 0,
  })
  const [activePreview, setActivePreview] = useState(null)
  const [showSapConfig, setShowSapConfig] = useState(false)
  const [sapConfigExists, setSapConfigExists] = useState(false)

  // Function to check if SAP config file exists
  const checkSapConfigExists = async () => {
    console.log("checkSapConfigExists: Starting file existence check...")
    if (window.electron && window.electron.ipcRenderer) {
      try {
        // Extract the project root from the current location
        // For Electron, the href typically looks like: file:///C:/Users/sp_za/Desktop/kazem/compass/frontend/renderer/main-chat/index.html
        const currentPath = window.location.href
        // Extract base path by removing the file:// protocol and going up to project root
        let basePath = currentPath.replace("file:///", "").replace(/\\/g, "/")

        // Navigate up to project root (remove /frontend/renderer/main-chat/index.html)
        const pathParts = basePath.split("/")
        // Find the compass directory index
        const compassIndex = pathParts.findIndex((part) => part === "compass")
        if (compassIndex !== -1) {
          basePath = pathParts.slice(0, compassIndex + 1).join("/")
        } else {
          // Fallback: assume we're in frontend and go up directories
          basePath = pathParts.slice(0, -3).join("/") // Remove /frontend/renderer/main-chat
        }

        const relativePath = "models/.sapConfig.yml"
        const absolutePath = basePath + "/" + relativePath
        console.log("checkSapConfigExists: Built absolute path:", absolutePath)

        // Use read-file API to check if file exists
        const result = await window.electron.ipcRenderer.invoke(
          "read-file",
          absolutePath
        )

        // If read-file succeeds, the file exists
        const fileExists = result.success || false
        console.log("checkSapConfigExists: Returning fileExists =", fileExists)
        return fileExists
      } catch (error) {
        console.log("Error checking if SAP config file exists:", error)
        return false
      }
    }
    console.log("checkSapConfigExists: Electron API not available")
    return false
  }

  useEffect(() => {
    console.log("MessageInput - Component mounted or updated")
    console.log("Current agentState:", agent.status)
    console.log("Current chat state:", chat)
    setMessage(chat.currentInput)

    // Check if SAP config file actually exists
    const checkFileAndSetState = async () => {
      console.log("checkFileAndSetState: Starting...")
      const fileExists = await checkSapConfigExists()
      console.log("MessageInput - File exists check result:", fileExists)
      console.log(
        "MessageInput - About to call setSapConfigExists with:",
        fileExists
      )
      setSapConfigExists(fileExists)
      console.log("MessageInput - setSapConfigExists called")
    }

    checkFileAndSetState()
  }, [agent, chat])

  // Add effect to handle clicks outside the dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isMenuOpen && !event.target.closest(".dropdown-container")) {
        setIsMenuOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isMenuOpen])

  const resetAgentState = () => {
    setMessage("")
    dispatch({
      type: ActionTypes.SET_CHAT_INPUT,
      payload: "",
    })
  }

  const handleChange = (e) => {
    const newMessage = e.target.value
    setMessage(newMessage)
    dispatch({
      type: ActionTypes.SET_CHAT_INPUT,
      payload: newMessage,
    })

    // Adjust height and toggle scrollbar dynamically
    const textarea = textareaRef.current
    textarea.style.height = "44px" // Reset to single-line height
    textarea.style.height = `${textarea.scrollHeight}px` // Grow dynamically

    if (
      textarea.scrollHeight > textarea.offsetHeight &&
      textarea.scrollHeight > 96
    ) {
      textarea.classList.add("overflow") // Add scrollbar after 4 lines
    } else {
      textarea.classList.remove("overflow") // Hide scrollbar if less than 4 lines
    }
  }

  const handleImageUpload = (event) => {
    const files = Array.from(event.target.files)
    files.forEach((file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const base64Data = e.target.result
        const cleanBase64 = base64Data.replace(
          /^data:image\/[a-z]+;base64,/,
          ""
        )
        setImages((prev) => [
          ...prev,
          { data: cleanBase64, preview: base64Data },
        ])
      }
      reader.readAsDataURL(file)
    })
    // Reset input so same file can be uploaded again
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handlePaste = (e) => {
    const items = e.clipboardData?.items
    if (items) {
      for (let item of items) {
        if (item.type.indexOf("image") !== -1) {
          const file = item.getAsFile()
          const reader = new FileReader()
          reader.onload = (e) => {
            const base64Data = e.target.result
            const cleanBase64 = base64Data.replace(
              /^data:image\/[a-z]+;base64,/,
              ""
            )
            setImages((prev) => [
              ...prev,
              { data: cleanBase64, preview: base64Data },
            ])
          }
          reader.readAsDataURL(file)
          e.preventDefault()
          break
        }
      }
    }
  }

  const handleSubmit = async (e) => {
    e?.preventDefault()

    if (!message.trim() || agent.status !== AgentStatus.STOPPED) {
      console.log("MessageInput - handleSubmit cancelled:", {
        hasMessage: !!message.trim(),
        agentStatus: agent.status,
      })
      return
    }

    try {
      console.log("MessageInput - Dispatching user message")

      dispatch({
        type: ActionTypes.ADD_CHAT_MESSAGE,
        payload: {
          type: "user",
          text: message.trim(),
          images: images.map((img) => img.data),
          timestamp: new Date().toISOString(),
        },
      })

      WebSocketService.sendMessage({
        text: message,
        images: images.map((img) => img.data),
      })

      setImages([])
      dispatch({
        type: ActionTypes.SET_CHAT_INPUT,
        payload: "",
      })

      const textarea = textareaRef.current
      textarea.style.height = "44px"
    } catch (error) {
      console.error("MessageInput - error sending message:", error)
    }
  }

  const handleStop = () => {
    dispatch({
      type: "STOP_PROCESSING",
      payload: "",
    })
    resetAgentState()
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const isInputEnabled = agent.status === AgentStatus.STOPPED

  const clearImage = (idx) => {
    setImages((prev) => {
      const newImages = prev.filter((_, i) => i !== idx)
      if (newImages.length === 0) {
        // Clear tooltip when removing last image
        setTooltipPosition({ show: false, x: 0, y: 0 })
        setActivePreview(null)
      }
      return newImages
    })
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleOptionClick = (option) => {
    setIsMenuOpen(false)
    switch (option) {
      case "Upload Photo":
        fileInputRef.current.click()
        break
      case "Upload File":
      case "Take Photo":
        console.log(`${option} feature coming soon`)
        break
    }
  }

  const handleMouseEnter = (e, preview) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setTooltipPosition({
      show: true,
      x: rect.left + rect.width / 2 - 100, // center tooltip
      y: rect.top - 160, // position above the image preview
    })
    setActivePreview(preview)
  }

  const handleMouseLeave = () => {
    setTooltipPosition({ show: false, x: 0, y: 0 })
    setActivePreview(null)
  }

  // Add click handler for plus button
  const handlePlusClick = async (e) => {
    e.stopPropagation() // Prevent event bubbling

    // Check file existence before opening menu to ensure correct button label
    console.log(
      "handlePlusClick: Checking file existence before opening menu..."
    )
    const fileExists = await checkSapConfigExists()
    console.log("handlePlusClick: File exists check result:", fileExists)
    setSapConfigExists(fileExists)

    setIsMenuOpen(!isMenuOpen)
  }

  // Add handler for SAP configuration
  const openSapConfig = () => {
    setIsMenuOpen(false)
    setShowSapConfig(true)
  }

  const handleSapConfigSubmit = async () => {
    // Check if file exists after submission
    console.log(
      "MessageInput: handleSapConfigSubmit called - checking file existence"
    )
    const fileExists = await checkSapConfigExists()
    setSapConfigExists(fileExists)
    console.log("MessageInput: File exists:", fileExists)
    setShowSapConfig(false)
  }

  // Add effect to log state changes
  useEffect(() => {
    console.log(
      "MessageInput - sapConfigExists state changed to:",
      sapConfigExists
    )
  }, [sapConfigExists])

  return (
    <div className="message-input-container">
      <div className="image-preview-list">
        <div className="message-buttons left">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            style={{ display: "none" }}
          />
          <div className="dropdown-container">
            <button
              className="button plus-button"
              onClick={handlePlusClick}
              disabled={!isInputEnabled}
            >
              <FontAwesomeIcon icon={faPlus} />
            </button>
            {isMenuOpen && (
              <div className="dropdown-menu">
                <button
                  className="dropdown-item"
                  onClick={() => {
                    fileInputRef.current.click()
                    setIsMenuOpen(false)
                  }}
                >
                  Upload Image
                </button>
                <button className="dropdown-item" onClick={openSapConfig}>
                  {sapConfigExists ? "Edit SAP Setup" : "Init SAP Setup"}
                </button>
              </div>
            )}
          </div>
        </div>
        {images.map((img, idx) => (
          <div
            className="image-preview"
            key={idx}
            onMouseEnter={(e) => handleMouseEnter(e, img.preview)}
            onMouseLeave={handleMouseLeave}
          >
            <img src={img.preview} alt={`Preview ${idx}`} />
            <button className="clear-image" onClick={() => clearImage(idx)}>
              ×
            </button>
          </div>
        ))}
        {tooltipPosition.show && activePreview && (
          <div
            className="tooltip-preview"
            style={{
              backgroundImage: `url(${activePreview})`,
              left: tooltipPosition.x,
              top: tooltipPosition.y,
            }}
          />
        )}
      </div>

      <div className="input-row">
        <textarea
          ref={textareaRef}
          className="message-input"
          placeholder={
            !isCompassReady
              ? ""
              : agent.status === AgentStatus.STOPPED
              ? "Ask Compass ..."
              : "Processing..."
          }
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          rows="1"
          disabled={!isInputEnabled}
        />
      </div>

      {/* Add the SAP configuration modal */}
      <InitSapConfig
        isOpen={showSapConfig}
        onClose={() => setShowSapConfig(false)}
        onSubmit={handleSapConfigSubmit}
      />
    </div>
  )
}

export default MessageInput
