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
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [showWorkflowSubmenu, setShowWorkflowSubmenu] = useState(false)
  const [closeTimeout, setCloseTimeout] = useState(null)
  const isCompassReady = connection.connected //&& agent.status === AgentStatus.STOPPED
  const workflowList = state.workflows || []
  const [tooltipPosition, setTooltipPosition] = useState({
    show: false,
    x: 0,
    y: 0,
  })
  const [activePreview, setActivePreview] = useState(null)
  const [showSapConfig, setShowSapConfig] = useState(false)
  const [sapConfigSubmitted, setSapConfigSubmitted] = useState(false)

  // Function to check if SAP config file exists
  const checkSapConfigExists = async () => {
    if (window.electron && window.electron.ipcRenderer) {
      try {
        const result = await window.electron.ipcRenderer.invoke(
          "read-file",
          "./models/.sapConfig.yml"
        )
        return result.success
      } catch (error) {
        console.log("SAP config file doesn't exist:", error)
        return false
      }
    }
    return false
  }

  useEffect(() => {
    console.log("MessageInput - Component mounted or updated")
    console.log("Current agentState:", agent.status)
    console.log("Current chat state:", chat)
    setMessage(chat.currentInput)

    // Check if SAP config file actually exists
    const checkFileAndSetState = async () => {
      const fileExists = await checkSapConfigExists()
      if (fileExists) {
        // File exists, mark as submitted
        setSapConfigSubmitted(true)
        localStorage.setItem("sapConfigSubmitted", "true")
      } else {
        // File doesn't exist, reset state
        setSapConfigSubmitted(false)
        localStorage.removeItem("sapConfigSubmitted")
      }
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

  const handleWorkflowSelect = (workflowName) => {
    setSelectedWorkflow(workflowName)
    setIsMenuOpen(false)
  }

  const removeWorkflow = () => {
    setSelectedWorkflow(null)
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
        workflow_name: selectedWorkflow,
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
    if (workflowList.includes(option)) {
      handleWorkflowSelect(option)
    } else {
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
  }

  const handleWorkflowMenuEnter = () => {
    if (closeTimeout) {
      clearTimeout(closeTimeout)
      setCloseTimeout(null)
    }
    setShowWorkflowSubmenu(true)
  }

  const handleWorkflowMenuLeave = () => {
    const timeout = setTimeout(() => {
      setShowWorkflowSubmenu(false)
    }, 300) // 300ms delay before closing
    setCloseTimeout(timeout)
  }

  // Clean up timeout on component unmount
  useEffect(() => {
    return () => {
      if (closeTimeout) {
        clearTimeout(closeTimeout)
      }
    }
  }, [closeTimeout])

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
  const handlePlusClick = (e) => {
    e.stopPropagation() // Prevent event bubbling
    setIsMenuOpen(!isMenuOpen)
  }

  // Add handler for SAP configuration
  const openSapConfig = () => {
    setIsMenuOpen(false)
    setShowSapConfig(true)
  }

  const handleSapConfigSubmit = () => {
    // Mark as submitted in localStorage and state
    localStorage.setItem("sapConfigSubmitted", "true")
    setSapConfigSubmitted(true)
    setShowSapConfig(false)
  }

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
                  {sapConfigSubmitted ? "Edit SAP Setup" : "Init SAP Setup"}
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

      {selectedWorkflow && (
        <div className="workflow-pill-container">
          <div className="workflow-pill">
            <span>@{selectedWorkflow}</span>
            <button
              className="remove-workflow"
              onClick={removeWorkflow}
              title="Remove workflow"
            >
              ×
            </button>
          </div>
        </div>
      )}

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
