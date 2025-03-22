import React, { useRef, useState, useEffect } from "react";
import { useAppState } from "../../common/context/AppContext";
import "../styles/ChatHistory.scss";
import { AgentStatus, AgentMode, MESSAGE_TYPES } from "../../common/constants";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faTimes,
  faClock,
  faPenToSquare,
  faImage,
  faTerminal
} from "@fortawesome/free-solid-svg-icons";
import {
  FILE_EDIT_TOOLS_NAME,
  TOOL_ACTION_MAPPING,
} from "../constants/toolActionMappings";
import WorkspaceWindow from "./workspace/workspace";
import { formatScriptForPlatform, getNameFromPath } from "./../../utils/utils";
import { v4 as uuidv4 } from "uuid";
import ReactMarkdown from 'react-markdown';

// Function to normalize markdown content by removing excessive newlines
const normalizeMarkdown = (content) => {
  if (!content) return '';
  
  // Simple replacement of all double newlines with single newlines
  return content.replace(/\n\n/g, '\n');
};

function ChatHistory({onEditorWidthChange }) {
  const { state } = useAppState();
  const { messages } = state.chat;
  const { agent: agentState } = state;
  const chatRef = useRef(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const isAutoMode = agentState.mode === AgentMode.AUTO;
  const [toolResults, setToolResults] = useState(new Map());
  const [expandedTools, setExpandedTools] = useState(new Set());
  const [previewCoord, setPreviewCoord] = useState({
    x: 0,
    y: 0,
    visible: false,
  });
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [editorTabs, setEditorTabs] = useState([]);
  const [isTerminalVisible, setIsTerminalVisible] = useState(false);
  const [terminalTabs, setTerminalTabs] = useState([]);

  useEffect(() => {
    console.log("ChatHistory - isTerminalVisible terminalTabs: ", isTerminalVisible, terminalTabs);
    if (terminalTabs.length === 0) {
      setIsTerminalVisible(false);
    }

  }, [terminalTabs]);

  const handleWorkspaceOpen = async (filePath, fileName, fileContent, toolId, terminalObj) => {
    // Check if the file is already being edited
    console.log("handleEditorOpen - terminalObj: ", terminalObj);
    console.log("handleEditorOpen - editorTabs: ", editorTabs);
    console.log("handleEditorOpen - terminalTabs: ", terminalTabs);
    console.log("handleEditorOpen - isTerminalVisible, isWorkspaceOpen, fileName: ",isTerminalVisible, isWorkspaceOpen, fileName);
    // Open the editor if not already open
    if (!isWorkspaceOpen) setIsWorkspaceOpen(true);

    if (terminalObj && terminalObj.isTerminal) {
      setEditorTabs((prev) => [...prev]); // Reset to ensure consistent rendering
      if (terminalObj.script && terminalTabs.length === 0) {
        setIsTerminalVisible(true);
        setTerminalTabs([
          {
            id: `term-1-${uuidv4()}`,
            name: "Terminal 1",
            command: terminalObj.script || "",
            isInitial: true,
          },
        ]);
      } 
      // else {
      //   setTerminalTabs((prev) => [...prev]);
      // }
      return;
    }

    const existingTabIndex = editorTabs.findIndex((tab) => tab.filePath === filePath);

    // Request file content from the main process
    const result = await window.electron.ipcRenderer.invoke('read-file', filePath);
    if (result.success) {
      fileContent = result.content;
    } else {
      console.error("Failed to read file:", result.error);
    }

    console.log("handleEditorOpen - fileName filePath: existingTabIndex toolId: ",fileName, filePath, existingTabIndex, toolId);
    if (existingTabIndex !== -1) {
      console.log("File already open in editor:", filePath);

      setEditorTabs((prev) =>
        prev.map((tab, index) =>
          index === existingTabIndex ? { ...tab, name: fileName, filePath, content: fileContent, originalContent: fileContent, isActive: true, id: toolId } : { ...tab, isActive: false }
        )
      );
      console.log("File already open in editorTabs:", editorTabs);
    } else {
      console.log("Opening new file in editor:", filePath);
      // Add a new tab to the editor
      setEditorTabs((prev) => [
        ...prev.map((tab) => ({ ...tab, isActive: false })), // Deactivate other tabs
        { filePath, name: fileName, content: fileContent, originalContent: fileContent, isActive: true, isInitial: true, isModified: false, id: toolId },
      ]);
      // Save the content to the file system
      window.electron.ipcRenderer.invoke("save-file", {
        filePath: filePath,
        content: fileContent,
      });
      console.log("Opening new file editorTabs:", editorTabs);
    }
  
  };

  const handleEditorClose = (tabs) => {
    console.log("handleEditorClose - tabs ", tabs);
    setEditorTabs(tabs); // Clear tabs
    setIsWorkspaceOpen(false); // Close the editor
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
    console.log("Rendering ChatHistory:", messages);
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
    console.log("renderToolUse - Tool name:", tool.name);
    console.log("renderToolUse - Tool input:", tool.input);
    console.log("Rendering WorkspaceWindow:", isWorkspaceOpen, editorTabs);

    const toolId = tool.id;
    const toolResult = toolResults.get(toolId);
    const isExpanded = expandedTools.has(toolId);

    const action = tool.input?.action || tool.name;
    console.log(
      "renderToolUse - Looking up action in TOOL_ACTION_MAPPING:",
      action
    );
    const filePath = tool.input?.path;
    const fileName = filePath ? getNameFromPath(filePath) : 'Untitled';
    let script = tool.input?.script || null;
    if (script) {
      script = formatScriptForPlatform(window.electron.platform, script);
      console.log("renderToolUse - script:", script);
    }

    // Debug the tool mapping itself
    console.log("TOOL_ACTION_MAPPING keys:", Object.keys(TOOL_ACTION_MAPPING));
    console.log("Looking up tool in mapping:", TOOL_ACTION_MAPPING[action]);

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
    const isWorkspaceTool = FILE_EDIT_TOOLS_NAME.includes(action);
    const toolHasBash = action === "bash_run";

    console.log("ChatHistory - renderToolUse: isWorkspaceTool toolHasBash isTerminalVisible", isWorkspaceTool, toolHasBash, isTerminalVisible);
    console.log("ChatHistory - renderToolUse: toolResult", toolResult);
    console.log("ChatHistory - renderToolUse: description", description);
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
              {isWorkspaceTool && (
                <button
                  className="popup-open-btn"
                  onClick={() => {
                    handleWorkspaceOpen(
                      filePath || "Untitled",
                      fileName,
                      tool.input?.file_text || "",
                      toolId,
                      {isTerminal: toolHasBash, script}                    
                    );
                  }}
                >
                  <FontAwesomeIcon icon={ toolHasBash ? faTerminal : faPenToSquare } />
                </button>
              )}
            </div>
            {isWorkspaceTool && isWorkspaceOpen && (
              <WorkspaceWindow
                isOpen={isWorkspaceOpen}
                isTerminalVisible={isTerminalVisible}
                setTerminalTabs={setTerminalTabs}
                terminalTabs={terminalTabs}
                tabs={editorTabs}
                onClose={handleEditorClose}
                onSave={(tabs) => {
                  console.log("ChatHistory - onSave", tabs);
                  setEditorTabs(tabs);
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
          <div className="message ai-message">
            <div className="message-content copyable-text markdown-content">
              <ReactMarkdown>{normalizeMarkdown(msg.content)}</ReactMarkdown>
            </div>
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
          <div className="message ai-message">
            <div className="message-content copyable-text markdown-content">
              <ReactMarkdown>{normalizeMarkdown(streamingText)}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatHistory;
