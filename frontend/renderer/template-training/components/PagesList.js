import {
  faEdit,
  faImage,
  faPlus,
  faTrash,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useState } from "react"
import WebSocketService from "../../common/services/websocket"
import "../styles/components/PagesList.scss"

const PagesList = ({ agentName, onAddPage, onEditPage }) => {
  const [pages, setPages] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    console.log("PagesList useEffect running for agent:", agentName)
    setIsLoading(true)

    const screenshotsHandler = (data) => {
      console.log("🎯 Screenshots handler called with data:", data)
      try {
        if (data && Array.isArray(data.screenshots)) {
          console.log("✅ Valid screenshots data received:", data.screenshots)
          setPages(data.screenshots)
        } else {
          console.warn("⚠️ Invalid screenshots data format:", data)
          setPages([])
        }
      } catch (error) {
        console.error("❌ Error handling screenshots data:", error)
        setPages([])
      } finally {
        console.log("🏁 Setting loading state to false")
        setIsLoading(false)
      }
    }

    const deletePageHandler = (data) => {
      console.log("🗑️ Delete page result:", data)
      if (data.success) {
        console.log("✅ Page deleted successfully:", data.message)
        // Remove the deleted page from the local state
        setPages(prevPages => prevPages.filter(page => page.id !== data.pageId))
        
        // Show success message
        if (data.message) {
          alert(data.message)
        }
      } else {
        console.error("❌ Page deletion failed:", data.message)
        alert(`Failed to delete page: ${data.message}`)
      }
    }

    // Set up the handlers
    WebSocketService.stateHandlers.onScreenshotsList = new Set([
      screenshotsHandler,
    ])
    WebSocketService.stateHandlers.onDeletePageResult = new Set([
      deletePageHandler,
    ])

    // Request screenshots if we have an agent name
    if (agentName) {
      console.log("🔍 Requesting screenshots for agent:", agentName)
      WebSocketService.getScreenshots(agentName)
    } else {
      console.log("⚠️ No agent name provided, clearing loading state")
      setIsLoading(false)
    }

    // Cleanup handlers when component unmounts
    return () => {
      WebSocketService.stateHandlers.onScreenshotsList.clear()
      WebSocketService.stateHandlers.onDeletePageResult.clear()
    }
  }, [agentName])

  const handleDeletePage = (page, e) => {
    e.stopPropagation()
    const pageName = page.name || "Untitled"
    const confirmMessage = `Delete page "${pageName}"?\n\nThis will also delete all associated templates for this page.`
    
    if (confirm(confirmMessage)) {
      console.log("🗑️ Deleting page:", page)
      WebSocketService.deletePage(page.id)
    }
  }



  const handleEditPage = (page, e) => {
    if (e) e.stopPropagation()
    onEditPage(page)
  }

  if (isLoading) {
    return (
      <div className="pages-list">
        <div className="pages-header">
          <h2>Pages</h2>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div>Loading pages for agent: {agentName}...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="pages-list">
      <div className="pages-header">
        <h2>Pages ({pages.length})</h2>
        <button className="btn-primary add-page-btn" onClick={onAddPage}>
          <FontAwesomeIcon icon={faPlus} />
          Add New Page
        </button>
      </div>

      <div className="pages-container">
        {pages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <FontAwesomeIcon icon={faImage} />
            </div>
            <h3>No pages found</h3>
            <p>
              Create your first page to start training the agent on UI
              components
            </p>
            <button className="btn-primary" onClick={onAddPage}>
              <FontAwesomeIcon icon={faPlus} />
              Create First Page
            </button>
          </div>
        ) : (
          <div className="pages-grid">
            {pages.map((page) => (
              <div
                key={page.id}
                className="page-card"
                onClick={() => handleEditPage(page)}
              >
                <div className="page-thumbnail">
                  <img
                    src={`data:image/png;base64,${page.image}`}
                    alt={page.name || `Page ${page.id}`}
                    onError={(e) => {
                      e.target.style.display = "none"
                      e.target.nextSibling.style.display = "flex"
                    }}
                  />
                  <div
                    className="thumbnail-fallback"
                    style={{ display: "none" }}
                  >
                    <FontAwesomeIcon icon={faImage} />
                  </div>
                </div>

                <div className="page-info">
                  <div className="page-title">
                    {page.name || "Untitled Page"}
                  </div>
                  <div className="page-meta">
                    <span className="page-date">
                      {page.created_at
                        ? new Date(page.created_at).toLocaleDateString()
                        : "Unknown date"}
                    </span>
                    <span className="page-elements">
                      {page.templates_count || 0} elements
                    </span>
                  </div>
                </div>

                <div className="page-actions">
                  <button
                    className="action-btn edit-btn"
                    onClick={(e) => handleEditPage(page, e)}
                    title="Edit Page"
                  >
                    <FontAwesomeIcon icon={faEdit} />
                  </button>

                  <button
                    className="action-btn delete-btn"
                    onClick={(e) => handleDeletePage(page, e)}
                    title="Delete Page"
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </button>
                </div>
              </div>
            ))}

            <div className="page-card add-card" onClick={onAddPage}>
              <div className="add-content">
                <div className="add-icon">
                  <FontAwesomeIcon icon={faPlus} />
                </div>
                <span>Add New Page</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PagesList
