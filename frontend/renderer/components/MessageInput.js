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
import { AgentStatus, ActionTypes } from '../constants'; 

function MessageInput() {
  const { state, dispatch } = useAppState();
  const { agent, chat } = state;
  const [message, setMessage] = useState(chat.currentInput);
  const textareaRef = useRef(null); // To dynamically measure the textarea height

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

  const handleSubmit = async (e) => {
    // Add logging at the start of submission
    console.log("MessageInput - Starting submission with message:", message);

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
          timestamp: new Date().toISOString(),
        },
      });

      // Add logging after dispatch
      //console.log("MessageInput - Message dispatched, sending to WebSocket");

      WebSocketService.sendMessage(message);
      setMessage("");
      dispatch({
        type: ActionTypes.SET_CHAT_INPUT,
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

  return (
    <div className="message-input-container">
      <textarea
        ref={textareaRef} // Reference to dynamically adjust height
        className="message-input"
        placeholder={
          agent.status === AgentStatus.STOPPED
            ? "Ask Compass ..."
            : "Processing..."
        }
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        rows="1"
        disabled={!isInputEnabled}
      />
      {/* <div className="message-buttons">
        <button
          className="button right-button"
          title="Send Message"
          onClick={ getPlayState() !== AgentStatus.STOPPED ? handleStop : handleSubmit}
          disabled={!isInputEnabled}
        >
          {(
            <FontAwesomeIcon icon={getPlayState() !== AgentStatus.STOPPED ? faStop : faArrowUp} />
          )}
        </button>
      </div> */}
    </div>
  );
}

export default MessageInput;
