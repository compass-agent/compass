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
  pageTitle, // Add pageTitle prop
}) => {
  const renderBreadcrumbs = () => {
    const items = []

    // Settings root (always first when not on SETTINGS view)
    items.push(
      <span
        key="settings"
        className={`nav-item ${
          currentView === VIEW_STATES.SETTINGS ? "active" : ""
        }`}
        onClick={() => onNavigate(VIEW_STATES.SETTINGS)}
      >
        Settings
      </span>
    )

    // If we're on settings root, just return it
    if (currentView === VIEW_STATES.SETTINGS) {
      return items
    }

    // Separator after Settings
    items.push(
      <FontAwesomeIcon
        key="sep-settings"
        icon={faChevronRight}
        className="separator"
      />
    )

    // Agent Hub
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
          {pageName || "New Page"}
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
