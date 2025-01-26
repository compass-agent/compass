import React, { useState, useEffect, useRef } from "react";
import WebSocketService from "../services/websocket";
import { useAppState } from "../context/AppContext";
import "../styles/MessageInput.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRotateRight,
  faArrowUp,
  faStop,
  faImage,
} from "@fortawesome/free-solid-svg-icons";
import { AgentStatus, ActionTypes } from '../constants'; 

function MessageInput() {
  const { state, dispatch } = useAppState();
  const { agent, chat } = state;
  const [message, setMessage] = useState(chat.currentInput);
  const [imageData, setImageData] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Add logging for initial render and state changes
  useEffect(() => {
    console.log("MessageInput - Component mounted or updated");
    console.log("Current agentState:", agent.status);
    console.log("Current chat state:", chat);
    setMessage(chat.currentInput);
  }, [agent, chat]);

  // Add effect to clear input when processing completes
  //SPZ TODO: it is commented. If working fine, remove it
  // useEffect(() => {
  //   if (agent.status === AgentStatus.STOPPED) {
  //     console.log("MessageInput - Clearing input after processing completed");
  //     resetAgentState();
  //   }
  // }, [agent.processing, agent.playing]);

  const resetAgentState = () => {
    setMessage("");
    dispatch({
      type: ActionTypes.SET_CHAT_INPUT,
      payload: "",
    });
   }

  const handleChange = (e) => {
    const newMessage = e.target.value;
    setMessage(newMessage);
    dispatch({
      type: ActionTypes.SET_CHAT_INPUT,
      payload: newMessage,
    });

    // Adjust height and toggle scrollbar dynamically
    const textarea = textareaRef.current;
    textarea.style.height = "44px"; // Reset to single-line height
    textarea.style.height = `${textarea.scrollHeight}px`; // Grow dynamically

    if (
      textarea.scrollHeight > textarea.offsetHeight &&
      textarea.scrollHeight > 96
    ) {
      textarea.classList.add("overflow"); // Add scrollbar after 4 lines
    } else {
      textarea.classList.remove("overflow"); // Hide scrollbar if less than 4 lines
    }
  };

  // const getPlayState = () => {
  //   const playState =
  //     !agent.processing && !agent.playing
  //       ? AgentStatus.STOPPED
  //       : agent.processing && agent.playing
  //       ? AgentStatus.RUNNING
  //       : AgentStatus.STOPPING;
  //   console.log("MessageInput - getPlayState:", playState, "agent:", agent);
  //   return playState;
  // };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64Data = e.target.result;
        // Strip the data URL prefix
        const cleanBase64 = base64Data.replace(/^data:image\/[a-z]+;base64,/, '');
        setImageData(cleanBase64);
        setImagePreview(base64Data); // Keep the full data URL for preview
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePaste = (e) => {
    const items = e.clipboardData?.items;
    if (items) {
      for (let item of items) {
        if (item.type.indexOf('image') !== -1) {
          const file = item.getAsFile();
          const reader = new FileReader();
          reader.onload = (e) => {
            const base64Data = e.target.result;
            // Strip the data URL prefix
            const cleanBase64 = base64Data.replace(/^data:image\/[a-z]+;base64,/, '');
            setImageData(cleanBase64);
            setImagePreview(base64Data); // Keep the full data URL for preview
          };
          reader.readAsDataURL(file);
          e.preventDefault();
          break;
        }
      }
    }
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    //const playState = getPlayState();

    if (!message.trim() || agent.status !== AgentStatus.STOPPED) {
      console.log("MessageInput - handleSubmit cancelled:", {
        hasMessage: !!message.trim(),
        agentStatus: agent.status,
      });
      return;
    }

    try {
      // Add logging before dispatch
      console.log("MessageInput - Dispatching user message");

      dispatch({
        type: ActionTypes.ADD_CHAT_MESSAGE,
        payload: {
          type: "user",
          text: message.trim(),
          image: imageData,
          timestamp: new Date().toISOString(),
        },
      });

      WebSocketService.sendMessage({
        text: message,
        image_data: imageData
      });

      setMessage("");
      setImageData(null);
      setImagePreview(null);
      dispatch({
        type: ActionTypes.SET_CHAT_INPUT,
        payload: "",
      });
      
      const textarea = textareaRef.current;
      textarea.style.height = "44px";
    } catch (error) {
      console.error("MessageInput - error sending message:", error);
    }
  };

  const handleStop = () => {
    dispatch({
      type: "STOP_PROCESSING",
      payload: "",
    });
    // Clear the message input and update the state
    resetAgentState();
  };
  
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isInputEnabled = agent.status === AgentStatus.STOPPED;

  const clearImage = () => {
    setImageData(null);
    setImagePreview(null);
  };

  return (
    <div className="message-input-container">
      {imagePreview && (
        <div className="image-preview">
          <img src={imagePreview} alt="Preview" />
          <button className="clear-image" onClick={clearImage}>×</button>
        </div>
      )}
      <div className="input-row">
        <div className="message-buttons left">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <button
            className="button image-button"
            onClick={() => fileInputRef.current.click()}
            disabled={!isInputEnabled}
          >
            <FontAwesomeIcon icon={faImage} />
          </button>
        </div>
        <textarea
          ref={textareaRef}
          className="message-input"
          placeholder={
            agent.status === AgentStatus.STOPPED
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
    </div>
  );
}

export default MessageInput;
