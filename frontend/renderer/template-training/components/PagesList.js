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

    // Set up the handler using the proper method
    WebSocketService.addHandler("onScreenshotsList", screenshotsHandler)

    // Request screenshots if we have an agent name
    if (agentName) {
      WebSocketService.getScreenshots(agentName)
    } else {
      setIsLoading(false)
    }

    // Cleanup handler when component unmounts
    return () => {
      WebSocketService.removeHandler("onScreenshotsList", screenshotsHandler)
    }
  }, [agentName])

  const handleDeletePage = (page, e) => {
    e.stopPropagation()
    if (confirm(`Delete page "${page.name || "Untitled"}"?`)) {
      // TODO: Implement delete functionality
      console.log("Delete page:", page)
    }
  }

  const handleDuplicatePage = (page, e) => {
    e.stopPropagation()
    // TODO: Implement duplicate functionality
    console.log("Duplicate page:", page)
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
