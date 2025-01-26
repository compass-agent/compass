import React, { useRef, useState, useEffect } from "react";
import { useAppState } from "../context/AppContext";
import "../styles/ChatHistory.scss";
import { MESSAGE_TYPES } from "../constants";
import { AgentStatus, AgentMode } from "../constants";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faTimes,
  faClock,
  faPenToSquare,
  faImage
} from "@fortawesome/free-solid-svg-icons";
import {
  FILE_EDIT_TOOLS_NAME,
  TOOL_ACTION_MAPPING,
} from "../constants/toolActionMappings";
import PopupFileEditor from "./workspace/fileEditor";


function ChatHistory({onEditorWidthChange }) {
  const { state } = useAppState();
  const { messages } = state.chat;
  const { agent: agentState } = state;
  const chatRef = useRef(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const isAutoMode = agentState.mode === AgentMode.AUTO;
  const [toolResults, setToolResults] = useState(new Map()); // Store tool results by ID
  const [expandedTools, setExpandedTools] = useState(new Set());
  const [previewCoord, setPreviewCoord] = useState({
    x: 0,
    y: 0,
    visible: false,
  });
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editorTabs, setEditorTabs] = useState([]); // Tracks files being edited

  const handleEditorOpen = (filePath, fileName, fileContent) => {
    // Check if the file is already being edited
    const existingTabIndex = editorTabs.findIndex((tab) => tab.filePath === filePath);
    console.log("handleEditorOpen - filePath: existingTabIndex: ", filePath, existingTabIndex);
    console.log("handleEditorOpen - editorTabs: ", editorTabs);
    if (existingTabIndex !== -1) {
      console.log("File already open in editor:", filePath);
      // Activate the existing editor tab
      setEditorTabs((prev) =>
        prev.map((tab, index) =>
          index === existingTabIndex ? { ...tab, name: fileName, filePath, content: fileContent, originalContent: fileContent, isActive: true } : { ...tab, isActive: false }
        )
      );
    } else {
      console.log("Opening new file in editor:", filePath);
      // Add a new tab to the editor
      setEditorTabs((prev) => [
        ...prev.map((tab) => ({ ...tab, isActive: false })), // Deactivate other tabs
        { filePath, name: fileName, content: fileContent, originalContent: fileContent, isActive: true, isModified: false },
      ]);
    }
  
    // Open the editor if not already open
    if (!isEditorOpen) setIsEditorOpen(true);
  };

  const handleEditorClose = (wasSaved, tabs) => {
    setEditorTabs(tabs); // Clear tabs
    setIsEditorOpen(false); // Close the editor
  };
  // TODO: Issue: this state is defined locally. to be able use it in chatInput.js,
  // it should be defined in the context or common parent component (AppContent)
  // console.log('ChatHistory - Current messages:', messages);
  // Add scroll to bottom effect: as the new chat is added
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [state.chat.messages, streamingText]);

  // Update streaming text handling
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.type === "ai_response_stream") {
        if (lastMessage.is_final) {
          setStreamingText("");
        } else {
          setStreamingText((prev) => prev + lastMessage.content);
        }
      }
    }
  }, [messages]);

  // Add logging to tool results effect
  useEffect(() => {
    console.log("Tool Results Effect - Current toolResults:", toolResults);
    console.log("Tool Results Effect - Processing messages:", messages);

    const newToolResults = new Map(toolResults);
    messages.forEach((msg) => {
      console.log("Processing message:", msg);
      if (msg.type === MESSAGE_TYPES.TOOL_RESULT) {
        console.log("Raw tool result message:", msg);
        console.log("Tool result content:", msg.content);
        console.log("Tool use ID:", msg.toolUseId);

        if (msg.toolUseId) {
          console.log("Setting tool result for ID:", msg.toolUseId);
          newToolResults.set(msg.toolUseId, {
            isError: msg.isError,
            result: msg.content,
          });
        } else {
          console.warn("Tool result message missing toolUseId:", msg);
        }
      }
    });

    if (newToolResults.size !== toolResults.size) {
      console.log("Updating tool results:", Object.fromEntries(newToolResults));
      setToolResults(newToolResults);
    }
  }, [messages]);

  // Add the missing getRecentMessages function
  const getRecentMessages = () => {
    if (!messages.length) return [];

    // Find the index of the most recent AI response
    const lastAiIndex = [...messages]
      .reverse()
      .findIndex((msg) => msg.type === MESSAGE_TYPES.AI_RESPONSE);

    if (lastAiIndex === -1) {
      // If no AI response found, return just the last message
      return messages.slice(-1);
    }

    // Return the AI response and all subsequent messages
    return messages.slice(-(lastAiIndex + 1));
  };

  const toggleToolExpansion = (toolId) => {
    setExpandedTools((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(toolId)) {
        newSet.delete(toolId);
      } else {
        newSet.add(toolId);
      }
      return newSet;
    });
  };

  const handleFileClick = (filePath) => {
    // Send IPC message to main process to open file
    window.electron.ipcRenderer.send("open-file", filePath);
  };

  const renderToolUse = (tool) => {
    console.log("renderToolUse - Received tool:", tool);
    //setIsEditorOpen(false);

    const toolId = tool.id;
    const toolResult = toolResults.get(toolId);
    const isExpanded = expandedTools.has(toolId);

    const action = tool.input?.action || tool.name;
    console.log(
      "renderToolUse - Looking up action in TOOL_ACTION_MAPPING:",
      action
    );
    const filePath = tool.input?.path;
    const fileName = filePath ? filePath.split('/').pop() : 'Untitled';

    const toolInfo = TOOL_ACTION_MAPPING[action] || {
      label: "Unknown Action",
      description: () => "Performing action",
    };

    const labelContent =
      typeof toolInfo.label === "function"
        ? toolInfo.label(tool)
        : toolInfo.label;

    const description = toolInfo.description(tool);
    const hasExpandableContent =
      description &&
      (description.text ||
        description.component ||
        (typeof description === "string" && description.length > 0));
    const isFileEditorTool = FILE_EDIT_TOOLS_NAME.includes(tool.input?.command);
    // Local state to track the visibility of the editor
    return (
      <div className="tool-suggestion">
        <div
          className="tool-header"
          onClick={() => hasExpandableContent && toggleToolExpansion(toolId)}
          style={{ cursor: hasExpandableContent ? "pointer" : "default" }}
        >
          <div className="tool-header-content">
            {hasExpandableContent && (
              <span className="expand-icon">{isExpanded ? "▼" : "▶"}</span>
            )}
            <span
              className="tool-label"
              onClick={(e) => {
                // Prevent expansion toggle when clicking the file link
                if (e.target.classList.contains("file-link")) {
                  e.stopPropagation();
                  handleFileClick(filePath);
                }
              }}
            >
              {labelContent}
            </span>
          </div>
          <span className="tool-status">
            {toolResult ? (
              toolResult.isError ? (
                <FontAwesomeIcon icon={faTimes} className="error" />
              ) : (
                <FontAwesomeIcon icon={faCheck} className="success" />
              )
            ) : (
              <FontAwesomeIcon icon={faClock} className="pending" />
            )}
          </span>
        </div>
        {isExpanded && hasExpandableContent && (
          <div className="tool-details">
            <div className="tool-input-row">
              <div className="tool-input-value">
                {typeof description === "object" ? (
                  <>
                    {description.text}
                    {description.component}
                  </>
                ) : (
                  description
                )}
              </div>
              {isFileEditorTool && (
                <button
                  className="popup-open-btn"
                  onClick={() => {
                    handleEditorOpen(
                      filePath || "Untitled",
                      fileName,
                      tool.input?.file_text || ""
                    );
                  }}
                >
                  <FontAwesomeIcon icon={faPenToSquare} />
                </button>
              )}
            </div>
            {isFileEditorTool && isEditorOpen && (
              <PopupFileEditor
                isOpen={isEditorOpen}
                tabs={editorTabs}
                onClose={handleEditorClose}
                onSave={(newContent) => {
                  const activeTabIndex = editorTabs.findIndex((tab) => tab.isActive);
                  if (activeTabIndex !== -1) {
                    setEditorTabs((prev) =>
                      prev.map((tab, index) =>
                        index === activeTabIndex ? { ...tab, fileContent: newContent } : tab
                      )
                    );
                  }
                }}
                onWidthChange={(newWidth) => onEditorWidthChange(newWidth)}
              />
            )}
          </div>
        )}
      </div>
    );
  };

  const renderMessage = (msg, agentState) => {
    console.log("renderMessage - Full message object:", msg);

    switch (msg.type) {
      case MESSAGE_TYPES.USER:
        if (!msg.text) return null;
        return (
          <div className="message user-message">
            <div
              className="message-content copyable-text"
              title={
                isAutoMode && agentState.status !== AgentStatus.STOPPED
                  ? msg.text
                  : ""
              }
            >
              {msg.text}
              {msg.image && (
                <span className="image-indicator">
                  <FontAwesomeIcon icon={faImage} />
                </span>
              )}
            </div>
          </div>
        );

      case MESSAGE_TYPES.AI_RESPONSE:
        if (!msg.content) return null;
        return (
          <div className="message">
            <div className="message-content copyable-text">{msg.content}</div>
          </div>
        );

      case MESSAGE_TYPES.AI_RESPONSE_STREAM:
        // Don't render individual stream messages
        return null;

      case MESSAGE_TYPES.TOOL_RESULT:
        // Don't render tool results as separate messages
        return null;

      case MESSAGE_TYPES.TOOL_USE_GROUP:
        console.log("renderMessage - Processing tool_use_group:", {
          tools: msg.tools,
          content: msg.content,
        });
        return (
          <div className="tool-suggestion-group">
            {(msg.tools || []).map((tool, index) => (
              <React.Fragment key={tool.id || index}>
                {renderToolUse(tool)}
              </React.Fragment>
            ))}
          </div>
        );

      default:
        return (
          <div
            className="message-content copyable-text"
            title={
              isAutoMode && agentState.status !== AgentStatus.STOPPED
                ? msg.text
                : ""
            }
          >
            {msg.text}
          </div>
        );
    }
  };

  return (
    <div className="chat-history-container">
      <div ref={chatRef} className="chat-history">
        {(isCollapsed ? getRecentMessages() : messages).map((msg, index) => (
          <React.Fragment key={index}>
            {renderMessage(msg, agentState)}
          </React.Fragment>
        ))}
        {/* Add streaming text display */}
        {streamingText && (
          <div className="message">
            <div className="message-content copyable-text">{streamingText}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatHistory;
