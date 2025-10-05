import {
  faFolderOpen,
  faPlus,
  faTerminal,
  faXmark,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react"
import Editor from "@monaco-editor/react"
import React, { useEffect, useRef, useState } from "react"
import { v4 as uuidv4 } from "uuid"
import {
  ButtonsBarHeight,
  WorkspaceWindowsConf,
} from "../../../common/constants"
import { getNameFromPath } from "../../../utils/utils"
import "../../styles/workspace.scss"
import TerminalComponent from "./terminal"

const WorkspaceWindow = ({
  isOpen,
  isTerminalVisible: initialTerminalVisible,
  setTerminalTabs,
  terminalTabs,
  tabs: initialTabs,
  onClose,
  onSave,
  onWidthChange,
}) => {
  const [workspaceWidth, setWorkspaceWidth] = useState(
    WorkspaceWindowsConf.MIN_EDITOR_WIN_WIDTH
  ) // Initial width of the editor
  const [isResizing, setIsResizing] = useState(false)
  const [tabs, setTabs] = useState(initialTabs)
  const [activeTab, setActiveTab] = useState(0)
  const activeTabRef = useRef(activeTab)
  const tabsRef = useRef([]) // Refs to measure individual tab widths
  const [canAddTab, setCanAddTab] = useState(true)
  const [terminalHeight, setTerminalHeight] = useState(
    WorkspaceWindowsConf.MIN_TERMINAL_WIN_HEIGHT
  )
  const [isTerminalVisible, setIsTerminalVisible] = useState(
    initialTerminalVisible
  )
  const isResizingTerminal = useRef(false)
  const hasMounted = useRef(false)

  useEffect(() => {
    console.log(
      "Workspace: initialTerminalVisible terminalTabs, isTerminalVisible",
      {
        terminalTabs,
        isTerminalVisible,
      }
    )
    if (terminalTabs.length > 0) setIsTerminalVisible(true)
  }, [initialTerminalVisible])

  useEffect(() => {
    console.log("Workspace:  isTerminalVisible", {
      terminalTabs,
      isTerminalVisible,
    })
  }, [isTerminalVisible])

  useEffect(() => {
    console.log("Workspace: terminalTabs", {
      terminalTabs,
      isTerminalVisible,
    })
    if (terminalTabs.length === 0) {
      setIsTerminalVisible(false)
    }
  }, [terminalTabs])

  useEffect(() => {
    setTabs(initialTabs)
    console.log("Workspace: initialTabs", initialTabs)
    if (initialTabs.length > 0) {
      initialTabs.forEach((tab, index) => {
        if (tab.isActive) {
          setActiveTab(index)
          activeTabRef.current = index
        }
      })
    }
  }, [initialTabs])

  useEffect(() => {
    console.log("workspace - Tabs updated:", tabs)
    if (tabs.length > 0) {
      tabsRef.current = tabs
      const newIndex = tabs.length - 1
      setActiveTab(newIndex)
      activeTabRef.current = newIndex
    }
  }, [tabs])

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)

    return () => {
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [])

  useEffect(() => {
    activeTabRef.current = activeTab
  }, [activeTab])
  // Update refs when tabs change
  useEffect(() => {
    tabsRef.current = tabs
    tabsRef.current = tabsRef.current.slice(0, tabs.length)
    updateCanAddTab() // Check tab accumulation on tabs update
  }, [tabs])

  const updateCanAddTab = () => {
    const panelWidth = workspaceWidth || 0
    const totalTabWidth = tabsRef.current.reduce(
      (acc, tab) => acc + (tab?.offsetWidth || 0),
      0
    )
    setCanAddTab(totalTabWidth + 100 <= panelWidth) // 70px for a new tab
  }

  //global
  useEffect(() => {
    console.log("Workspace: isOpen", isOpen)
    if (isOpen) {
      onWidthChange(WorkspaceWindowsConf.MIN_EDITOR_WIN_WIDTH)
      calcEditorWidth()
    }
  }, [isOpen])

  const handleMouseMove = (e) => {
    if (!isResizing) return
    calcEditorWidth(e)
  }

  const calcEditorWidth = (e = null) => {
    // Calculate the new width based on mouse position, with boundaries
    const newWidth = Math.min(
      Math.max(
        WorkspaceWindowsConf.MIN_EDITOR_WIN_WIDTH,
        window.innerWidth - (e ? e.clientX : workspaceWidth)
      ),
      WorkspaceWindowsConf.MAX_EDITOR_WIN_WIDTH
    )
    setWorkspaceWidth(newWidth)
    onWidthChange(newWidth) // Notify parent of width changes
  }

  const handleMouseUp = () => {
    setIsResizing(false)
  }

  // Attach and detach event listeners for resizing
  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", handleMouseMove)
      window.addEventListener("mouseup", handleMouseUp)
    } else {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isResizing])

  const openFile = async () => {
    try {
      const response = await window.electron.ipcRenderer.invoke(
        "open-file-dialog"
      )
      if (response.success) {
        const { filePath, fileName, content } = response
        console.log("Workspace: openFile", {
          filePath,
          fileName,
          content,
        })
        const newTab = {
          id: uuidv4(),
          name: fileName,
          filePath: filePath,
          content: content,
          originalContent: content,
        }
        setTabs([...tabs, newTab])
        setActiveTab(tabs.length) // Activate the new tab
      } else {
        console.error("Failed to open file dialog:", response.error)
      }
    } catch (error) {
      console.error("Error opening file dialog:", error)
    }
  }

  // Handle close with unsaved changes
  const handleClose = () => {
    console.log("Workspace: handleClose:", tabs)
    onClose(tabs)
    onWidthChange(0)
  }

  const handleAddTab = (
    name = `Tab ${tabs.length + 1}`,
    content = "",
    originalContent = "",
    filePath = "",
    isInitial = false
  ) => {
    const newTab = {
      id: uuidv4(),
      name: name,
      content: content,
      originalContent: originalContent,
      filePath: filePath,
      isModified: false,
      isInitial: isInitial,
    }

    const updatedTabs = [...tabs, newTab]
    console.info(
      "Workspace: handleAddTab: updatedTabs before setting",
      updatedTabs
    )
    setTabs(updatedTabs)
  }

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault() // Prevent default browser save behavior
      const activeTabIndex = activeTabRef.current
      setTabs((prevTabs) => {
        const updatedTabs = [...prevTabs]
        updatedTabs[activeTabIndex].isModified = false // Example modification
        return updatedTabs
      })
      const currentTabs = tabsRef.current // Access the latest state from the ref
      console.info(
        "Workspace: handleKeyDown: activeTabRef.current tabs",
        activeTabIndex,
        currentTabs
      )

      if (activeTabIndex === -1 || !currentTabs[activeTabIndex]) {
        console.warn("Workspace: No active tab to save")
        return
      }
      console.info("Workspace: handleSaveTab: tabs", tabs)
      handleSaveTab(activeTabIndex)
    }
  }

  const handleRemoveTab = async (index) => {
    const tab = tabs[index]
    console.log("", tab)
    if (tab.isModified) {
      const confirmClose = window.confirm(
        "You have unsaved changes. Do you want to save them before closing?"
      )
      if (confirmClose) {
        await handleSaveTab(index) // Save changes
      }
    }
    const updatedTabs = tabs.filter((_, i) => i !== index)
    setTabs(updatedTabs)
    // Only set activeTab if there are remaining tabs
    if (updatedTabs.length > 0) {
      setActiveTab(index === 0 ? 0 : index - 1) // Adjust active tab
    } else {
      setActiveTab(-1) // No tabs left, reset active tab
    }
  }

  const handleSaveTab = async (index) => {
    const currentTabs = tabsRef.current
    console.info(
      "Workspace: handleSaveTab: index currentTabs",
      index,
      currentTabs
    )
    console.info(
      "Workspace: handleSaveTab: currentTabs[index]",
      currentTabs[index]
    )
    if (!currentTabs[index].filePath) {
      console.info("Workspace: handleSaveTab: No file path")
      const filePath = await createFile(currentTabs[index])
      if (filePath) {
        currentTabs[index].filePath = filePath
        currentTabs[index].name = getNameFromPath(filePath)
        currentTabs[index].isModified = false
        setTabs(currentTabs)
      } else {
        console.error("Workspace:Failed to save new file")
        return
      }
    }
    if (currentTabs[index].isInitial) {
      //TODO: updatedTabs[index].name === fileName
      console.info("Workspace: handleSaveTab: isInitial")
      saveContentToFile(currentTabs[index])
    } else {
      saveContentToFile(currentTabs[index])
    }
    currentTabs[index].isModified = false
    currentTabs[index].originalContent = currentTabs[index].content
    setTabs(currentTabs)
    console.info("Workspace: handleSaveTab: currentTabs", currentTabs)
    console.info("Workspace: handleSaveTab: tabs", tabs)
    onSave(currentTabs)
  }

  const saveContentToFile = (tabToSave) => {
    // Save the content to the file system
    window.electron.ipcRenderer.invoke("save-file", {
      filePath: tabToSave.filePath,
      content: tabToSave.content,
    })
  }

  const createFile = async (tab) => {
    try {
      const response = await window.electron.ipcRenderer.invoke(
        "save-file-dialog",
        tab
      )
      if (response.success) {
        const { filePath } = response
        console.log("Workspace: saveFile", { filePath })
        return filePath
      } else {
        console.error("Workspace: Failed to save file:", response.error)
        return null
      }
    } catch (error) {
      console.error("Workspace: Error saving file:", error)
      return null
    }
  }
  // TERMINAL

  const toggleTerminal = () => {
    console.log(
      `Workspace - toggleTerminal: isTerminalVisible: ${isTerminalVisible}`
    )

    if (!isTerminalVisible) {
      setTerminalTabs([
        {
          id: `term-1-${uuidv4()}`,
          name: "Terminal 1",
          command: "", // Use command if available : terminalCommand ||
          isInitial: false, // Mark as initial if command exists : !!terminalCommand
        },
      ])
    }
    setIsTerminalVisible(!isTerminalVisible)
  }

  const handleTerminalResize = (e) => {
    if (!isResizingTerminal.current) return
    const newHeight = Math.max(
      WorkspaceWindowsConf.MIN_TERMINAL_WIN_HEIGHT,
      window.innerHeight - e.clientY
    )
    setTerminalHeight(newHeight)
  }

  const startResizingTerminal = (e) => {
    e.preventDefault()
    isResizingTerminal.current = true
    window.addEventListener("mousemove", handleTerminalResize)
    window.addEventListener("mouseup", stopResizingTerminal)
  }

  const stopResizingTerminal = () => {
    isResizingTerminal.current = false
    window.removeEventListener("mousemove", handleTerminalResize)
    window.removeEventListener("mouseup", stopResizingTerminal)
  }

  if (!isOpen) return null // Do not render when not open
  return (
    <div className="workspace-panel" style={{ width: `${workspaceWidth}px` }}>
      <div className="file-editor-container">
        <div className="file-editor-header">
          <div className="file-editor-header-top">
            <div className="file-editor-btn open-folder-btn" onClick={openFile}>
              <FontAwesomeIcon icon={faFolderOpen} />
            </div>
            <button
              onClick={toggleTerminal}
              className="file-editor-btn terminal-btn"
            >
              <FontAwesomeIcon icon={faTerminal} />
            </button>
            <button onClick={handleClose} className="file-editor-btn close-btn">
              <FontAwesomeIcon icon={faXmark} />
            </button>
          </div>
        </div>

        <TabGroup
          selectedIndex={activeTab}
          onChange={(index) => {
            setActiveTab(index)
            activeTabRef.current = index
          }}
        >
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
                    className={`close-tab-btn ${
                      tab.isModified ? "unsaved-indicator" : ""
                    }`}
                    title={tab.isModified ? "Unsaved changes" : "Close tab"}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveTab(index)
                    }}
                  >
                    <FontAwesomeIcon icon={faXmark} />
                  </span>
                </div>
              </Tab>
            ))}
            {canAddTab && (
              <button
                onClick={() => handleAddTab()}
                className="file-editor-btn add-tab-btn"
              >
                <FontAwesomeIcon icon={faPlus} />
              </button>
            )}
          </TabList>

          <TabPanels
            className="tab-panels"
            style={{
              height: isTerminalVisible
                ? `calc(${window.innerHeight}px - ${
                    3 * ButtonsBarHeight
                  }px - ${terminalHeight}px)`
                : `calc(${window.innerHeight}px - ${3 * ButtonsBarHeight}px)`,
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
                    const updatedTabs = [...tabs]
                    updatedTabs[index].content = value
                    updatedTabs[index].isModified =
                      value !== tabs[index].originalContent // Compare with original content
                    setTabs(updatedTabs)
                  }}
                />
              </TabPanel>
            ))}
          </TabPanels>
        </TabGroup>

        {/* Editor Resize Handle */}
        <div
          className="file-editor-resize-handle"
          onMouseDown={() => setIsResizing(true)}
          title="Drag to resize"
        ></div>
      </div>

      {isTerminalVisible && terminalTabs.length > 0 && (
        <div
          className="terminal-container"
          style={{
            width: `${workspaceWidth}px`,
            height: `${terminalHeight}px`,
            maxHeight: `calc(${window.innerHeight}px - ${
              2 * ButtonsBarHeight
            }px)`,
          }}
        >
          <TerminalComponent
            tabs={terminalTabs}
            terminalWidth={workspaceWidth}
            setTabs={setTerminalTabs}
          />
          <div
            className="terminal-resize-handle"
            onMouseDown={startResizingTerminal}
            title="Drag to resize terminal"
          ></div>
        </div>
      )}
    </div>
  )
}

export default WorkspaceWindow
