import React, { useState, useEffect, useRef } from "react";
import WebSocketService from "../services/websocket";
import { useAppState } from "../context/AppContext";
import "../styles/MessageInput.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faRotateRight,
  faArrowUp,
  faStop,
} from "@fortawesome/free-solid-svg-icons";
import { AgentStatus } from '../constants'; 

const PlayState = {
  STOPPED: "stopped",
  RUNNING: "running",
  STOPPING: "stopping",
};

function MessageInput() {
  const { state, dispatch } = useAppState();
  const { agent, chat } = state;
  const [message, setMessage] = useState("");
  const textareaRef = useRef(null); // To dynamically measure the textarea height

  // Add logging for initial render and state changes
  useEffect(() => {
    console.log("MessageInput - Component mounted or updated");
    console.log("Current agent state:", agent);
    console.log("Current chat state:", chat);
  }, [agent, chat]);

  // Add effect to clear input when processing completes
  useEffect(() => {
    if (!agent.processing && !agent.playing) {
      console.log("MessageInput - Clearing input after processing completed");
      resetAgentState();
    }
  }, [agent.processing, agent.playing]);

  const resetAgentState = () => {
    setMessage("");
    dispatch({
      type: "SET_CHAT_INPUT",
      payload: "",
    });
   }

  const handleChange = (e) => {
    const newMessage = e.target.value;
    setMessage(newMessage); // Update local state
    dispatch({
      type: "SET_CHAT_INPUT",
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

  const getPlayState = () => {
    const playState =
      !agent.processing && !agent.playing
        ? PlayState.STOPPED
        : agent.processing && agent.playing
        ? PlayState.RUNNING
        : PlayState.STOPPING;
    console.log("MessageInput - getPlayState:", playState, "agent:", agent);
    return playState;
  };

  const handleSubmit = async (e) => {
    // Add logging at the start of submission
    console.log("MessageInput - Starting submission with message:", message);

    e?.preventDefault();
    const playState = getPlayState();

    if (!message.trim() || playState !== PlayState.STOPPED) {
      console.log("MessageInput - handleSubmit cancelled:", {
        hasMessage: !!message.trim(),
        playState,
      });
      return;
    }

    try {
      // Add logging before dispatch
      console.log("MessageInput - Dispatching user message");

      dispatch({
        type: "ADD_CHAT_MESSAGE",
        payload: {
          type: "user",
          text: message.trim(),
          timestamp: new Date().toISOString(),
        },
      });

      // Add logging after dispatch
      console.log("MessageInput - Message dispatched, sending to WebSocket");

      WebSocketService.sendMessage(message);
      setMessage("");
      dispatch({
        type: "SET_CHAT_INPUT",
        payload: "",
      });
       // Reset the height of the textarea
      const textarea = textareaRef.current;
      textarea.style.height = "44px";

    } catch (error) {
      console.error("MessageInput - error sending message:", error);
    }
  };

  const handleStop = () => {
    console.log("MessageInput - Stopping the agent");
    dispatch({
      type: "STOP_PROCESSING",
      payload: "",
    });
    // Clear the message input and update the state
    resetAgentState();
  };
  
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      console.log("MessageInput - Enter key pressed");
      e.preventDefault();
      handleSubmit();
    }
  };

  const playState = getPlayState();
  console.log("MessageInput - Render:", {
    playState,
    message,
    isDisabled: playState !== PlayState.STOPPED,
  });

  const isInputEnabled = agent.status === AgentStatus.IDLE;

  return (
    <div className="message-input-container">
      <textarea
        ref={textareaRef} // Reference to dynamically adjust height
        className="message-input"
        placeholder={
          agent.status === AgentStatus.IDLE
            ? "Ask Compass ..."
            : "Processing..."
        }
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        rows="1"
        disabled={!isInputEnabled}
      />
      <div className="message-buttons">
        <button
          className="button right-button"
          title="Send Message"
          onClick={ getPlayState() !== PlayState.STOPPED ? handleStop : handleSubmit}
          disabled={!isInputEnabled}
        >
          {(
            <FontAwesomeIcon icon={getPlayState() !== PlayState.STOPPED ? faStop : faArrowUp} />
          )}
        </button>
      </div>
    </div>
  );
}

export default MessageInput;
