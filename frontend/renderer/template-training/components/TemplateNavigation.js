import { faChevronRight } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React from "react"
import { VIEW_STATES } from "../constants/viewStates"
import "../styles/components/TemplateNavigation.scss"

const TemplateNavigation = ({
  currentView,
  agentName,
  pageName,
  onNavigate,
  pageTitle,
  currentScreenshot,
}) => {
  const renderBreadcrumbs = () => {
    const items = []

    // If we're on SETTINGS view, show only Settings
    if (currentView === VIEW_STATES.SETTINGS) {
      items.push(
        <span key="settings" className="nav-item active">
          Settings
        </span>
      )
      return items
    }

    // For all other views, start with Agent Hub (no Settings breadcrumb)
    items.push(
      <span
        key="hub"
        className={`nav-item ${
          currentView === VIEW_STATES.AGENT_HUB ? "active" : ""
        }`}
        onClick={() => onNavigate(VIEW_STATES.AGENT_HUB)}
      >
        Agent Hub
      </span>
    )

    // Show Setup if we're past AGENT_HUB
    if (currentView !== VIEW_STATES.AGENT_HUB) {
      items.push(
        <FontAwesomeIcon
          key="sep1"
          icon={faChevronRight}
          className="separator"
        />
      )

      // Determine if we're creating or editing based on pageTitle
      const isCreating = pageTitle === "Create New Agent"
      const setupLabel = isCreating
        ? `Create ${agentName || "Agent"}`
        : `Edit ${agentName || "Agent"}`

      items.push(
        <span
          key="setup"
          className={`nav-item ${
            currentView === VIEW_STATES.SETUP ? "active" : ""
          }`}
          onClick={() => onNavigate(VIEW_STATES.SETUP)}
        >
          {setupLabel}
        </span>
      )
    }

    // Show Pages List if we're at PAGES_LIST or PAGE_EDITOR
    if (
      currentView === VIEW_STATES.PAGES_LIST ||
      currentView === VIEW_STATES.PAGE_EDITOR
    ) {
      items.push(
        <FontAwesomeIcon
          key="sep2"
          icon={faChevronRight}
          className="separator"
        />
      )
      items.push(
        <span
          key="pages"
          className={`nav-item ${
            currentView === VIEW_STATES.PAGES_LIST ? "active" : ""
          }`}
          onClick={() => onNavigate(VIEW_STATES.PAGES_LIST)}
        >
          Pages
        </span>
      )
    }

    // Show Page Editor if we're at PAGE_EDITOR
    if (currentView === VIEW_STATES.PAGE_EDITOR) {
      items.push(
        <FontAwesomeIcon
          key="sep3"
          icon={faChevronRight}
          className="separator"
        />
      )
      items.push(
        <span key="editor" className="nav-item active">
          {currentScreenshot && pageName ? pageName : "New Page"}
        </span>
      )
    }

    return items
  }

  return (
    <nav className="template-navigation">
      <div className="navigation-header">
        <div className="breadcrumbs">{renderBreadcrumbs()}</div>
      </div>
    </nav>
  )
}

export default TemplateNavigation
