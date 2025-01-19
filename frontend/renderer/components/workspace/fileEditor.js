import React, { useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import "../../styles/workspace.scss";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faXmark,
  faFloppyDisk,
  faFolderOpen,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import { ButtonsBarHeight, EditorWindowConf } from "../../constants";
import { Tab, TabGroup, TabList, TabPanels, TabPanel } from "@headlessui/react";
import { v4 as uuidv4 } from "uuid";

const FileEditorPanel = ({
  isOpen,
  fileContent,
  fileName,
  onClose,
  onSave,
  onWidthChange,
}) => {
  const [width, setWidth] = useState(EditorWindowConf.MIN_EDITOR_WIN_WIDTH); // Initial width of the editor
  const [isResizing, setIsResizing] = useState(false);
  const [content, setContent] = useState(fileContent);
  const [isModified, setIsModified] = useState(false); // Track unsaved changes
  const [tabs, setTabs] = useState([
    { id: 1, name: fileName, path: null, content: fileContent, originalContent: content, isModified: false, isInitial: true },
  ]);
  const [activeTab, setActiveTab] = useState(0);
  const activeTabRef = useRef(activeTab);
  const tabsRef = useRef([]); // Refs to measure individual tab widths
  const [canAddTab, setCanAddTab] = useState(true);

  useEffect(() => {
    activeTabRef.current = activeTab;
  }, [activeTab]);
  // Update refs when tabs change
  useEffect(() => {
    tabsRef.current = tabs;
    tabsRef.current = tabsRef.current.slice(0, tabs.length);
    updateCanAddTab(); // Check tab accumulation on tabs update
  }, [tabs]);

  const updateCanAddTab = () => {
    const panelWidth = width || 0;
    const totalTabWidth = tabsRef.current.reduce(
      (acc, tab) => acc + (tab?.offsetWidth || 0),
      0
    );
    setCanAddTab(totalTabWidth + 70 <= panelWidth); // 70px for a new tab
  };
  //global
  useEffect(() => {
    if (isOpen) {
      setContent(fileContent); // Update content if fileContent prop changes
      setIsModified(false); // Reset modification state
      onWidthChange(EditorWindowConf.MIN_EDITOR_WIN_WIDTH);
      calcEditorWidth();
    } else {
      setContent(fileContent);
    }
  }, [isOpen, fileContent]);

  const handleMouseDown = () => {
    setIsResizing(true);
  };

  const handleMouseMove = (e) => {
    if (!isResizing) return;
    calcEditorWidth(e);
  };

  const calcEditorWidth = (e = null) => {
    // Calculate the new width based on mouse position, with boundaries
    const newWidth = Math.min(
      Math.max(
        EditorWindowConf.MIN_EDITOR_WIN_WIDTH,
        window.innerWidth - (e ? e.clientX : width)
      ),
      EditorWindowConf.MAX_EDITOR_WIN_WIDTH
    );
    setWidth(newWidth);
    onWidthChange(newWidth); // Notify parent of width changes
  }

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  // Attach and detach event listeners for resizing
  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    } else {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [content]);

  const openFile = async () => {
    try {
      const response = await window.electron.ipcRenderer.invoke("open-file-dialog");
      if (response.success) {
        const { filePath, fileName, content } = response;
        console.log("Renderer Process: openFile", { filePath, fileName, content });
        const newTab = {
          id: uuidv4(),
          name: fileName,
          path: filePath,
          content: content,
          originalContent: content,
        };
        setTabs([...tabs, newTab]);
        setActiveTab(tabs.length); // Activate the new tab
      } else {
        console.error("Failed to open file dialog:", response.error);
      }
    } catch (error) {
      console.error("Error opening file dialog:", error);
    }
  };

  // Handle close with unsaved changes
  const handleClose = () => {

    onClose(false, content);
    onWidthChange(0);
  };

  const handleAddTab = () => {
    const newTab = {
      id: uuidv4(),
      name: `Tab ${tabs.length + 1}`,
      content: "",
      originalContent: "",
      isModified: false,
    };
    setTabs([...tabs, newTab]);
    setActiveTab(tabs.length); // Activate the new tab
  };

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault(); // Prevent default browser save behavior
      const activeTabIndex = activeTabRef.current;
      handleSaveTab(activeTabIndex);
    }
  };
  
  const handleRemoveTab = (index) => {
    const tab = tabs[index];
    console.log("", tab);
    if (tab.isModified) {
      const confirmClose = window.confirm(
        "You have unsaved changes. Do you want to save them before closing?"
      );
      if (confirmClose) {
        handleSaveTab(index); // Save changes
      }
    }
    if (tabs.length === 1) return; // Prevent removing the last tab
    const updatedTabs = tabs.filter((_, i) => i !== index);
    setTabs(updatedTabs);
    setActiveTab(index === 0 ? 0 : index - 1); // Adjust active tab
  };

  const handleSaveTab = async (index) => {
    const updatedTabs = [...tabsRef.current];
    if (!updatedTabs[index].path) {
      const filePath = await createFile(updatedTabs[index].content);
      if (filePath) {
        updatedTabs[index].path = filePath;
        updatedTabs[index].isModified = false; // Mark tab as saved
        setTabs(updatedTabs);
      } else {
        console.error("Failed to save new file");
        return;
      }
    }
    if (updatedTabs[index].isInitial && updatedTabs[index].name === fileName) {
      onInputTabSave(updatedTabs[index].content); // Pass the content to the parent for saving
    } else {
      saveContentToFile(updatedTabs[index]);
    }
  };

  const onInputTabSave = (content) => {
    // Find the tab with the fileName from Input
    if (content) {
      onSave(content); // Pass the content to the parent for saving
    }
  };

  const saveContentToFile = (tabToSave) => {
    // Save the content to the file system
    window.electron.ipcRenderer.invoke("save-file", {
      filePath: tabToSave.path,
      content: tabToSave.content,
    });
  };

  const createFile = async (content) => {
    try {
      const response = await window.electron.ipcRenderer.invoke("save-file-dialog", content);
      if (response.success) {
        const { filePath } = response;
        console.log("Renderer Process: saveFile", { filePath });
        return filePath;
      } else {
        console.error("Failed to save file:", response.error);
        return null;
      }
    } catch (error) {
      console.error("Error saving file:", error);
      return null;
    }
  };

  if (!isOpen) return null; // Do not render when not open
  return (
    <div className="file-editor-panel" style={{ width: `${width}px` }}>
      <div className="file-editor-header">
        <div className="file-editor-header-top">
          <div className="file-editor-btn open-folder-btn" onClick={openFile}>
            <FontAwesomeIcon icon={faFolderOpen} />
          </div>
          <button onClick={handleClose} className="file-editor-btn close-btn">
            <FontAwesomeIcon icon={faXmark} />
          </button>
        </div>
      </div>

      <TabGroup selectedIndex={activeTab} onChange={(index) => {
        setActiveTab(index);
        activeTabRef.current = index;
      }}>
        <TabList className="file-editor-tabs">
          {tabs.map((tab, index) => (
            <Tab
              key={tab.id}
              ref={(el) => (tabsRef.current[index] = el)} // Assign ref for each tab
              className={({ selected }) => `tab ${selected ? "active" : ""}`}
            >
              <div className="tab-content">
                <span className="tab-label" title={tab.name}>
                  {tab.name}
                </span>
                <span
                  className={`close-tab-btn ${tab.isModified ? "unsaved-indicator" : ""}`}
                  title={tab.isModified ? "Unsaved changes" : "Close tab"}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveTab(index);
                  }}
                >
                  <FontAwesomeIcon icon={faXmark} />
                </span>
              </div>
            </Tab>
          ))}
          {canAddTab && (
            <button
              onClick={handleAddTab}
              className="file-editor-btn add-tab-btn"
            >
              <FontAwesomeIcon icon={faPlus} />
            </button>
          )}
        </TabList>

        <TabPanels
          className="tab-panels"
          style={{
            height: `calc(${window.innerHeight}px - ${3 * ButtonsBarHeight}px)`,
          }}
        >
          {tabs.map((tab, index) => (
            <TabPanel key={tab.id} className="tab-panel">
              <Editor
                height="100%"
                width="100%"
                defaultLanguage="plaintext"
                value={tab.content}
                theme="vs-dark"
                onChange={(value) => {
                  const updatedTabs = [...tabs];
                  updatedTabs[index].content = value;
                  updatedTabs[index].isModified = value !== tabs[index].originalContent; // Compare with original content
                  setTabs(updatedTabs);
                  //setIsModified(true);
                }}
              />
            </TabPanel>
          ))}
        </TabPanels>
      </TabGroup>

      <div
        className="file-editor-resize-handle"
        onMouseDown={() => setIsResizing(true)}
        title="Drag to resize"
      ></div>
    </div>
  );
};

export default FileEditorPanel;
