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
    setIsLoading(true)

    const screenshotsHandler = (data) => {
      try {
        if (data && Array.isArray(data.screenshots)) {
          setPages(data.screenshots)
        } else {
          setPages([])
        }
      } catch (error) {
        console.error("Error handling screenshots data:", error)
        setPages([])
      } finally {
        setIsLoading(false)
      }
    }

    const deletePageHandler = (data) => {
      console.log("🗑️ Delete page result:", data)
      if (data.success) {
        console.log("✅ Page deleted successfully:", data.message)
        // Remove the deleted page from the local state
        setPages((prevPages) =>
          prevPages.filter((page) => page.id !== data.pageId)
        )

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
      WebSocketService.getScreenshots(agentName)
    } else {
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
        <button className="btn-primary add-page-btn" onClick={onAddPage}>
          <FontAwesomeIcon icon={faPlus} />
          New Page
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
          <div className="pages-table">
            <div className="table-header">
              <div className="col name">Name</div>
              <div className="col date">Date</div>
              <div className="col actions">Actions</div>
            </div>
            <div className="table-body">
              {pages.map((page) => (
                <div key={page.id} className="table-row">
                  <div className="col name">
                    <div
                      className="page-name"
                      onClick={() => handleEditPage(page)}
                    >
                      {page.name || "Untitled Page"}
                    </div>
                  </div>
                  <div className="col date">
                    {page.created_at
                      ? new Date(page.created_at).toLocaleDateString()
                      : "Unknown date"}
                  </div>
                  <div className="col actions">
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
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PagesList
