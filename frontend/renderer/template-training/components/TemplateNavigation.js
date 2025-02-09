import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronRight } from '@fortawesome/free-solid-svg-icons';
import '../styles/components/TemplateNavigation.scss';
import { VIEW_STATES } from '../constants/viewStates';

const TemplateNavigation = ({ currentView, agentName, pageName, onNavigate }) => {
  const renderBreadcrumbs = () => {
    const items = [];

    // Always show Agent Hub
    items.push(
      <span 
        key="hub" 
        className={`nav-item ${currentView === VIEW_STATES.AGENT_HUB ? 'active' : ''}`}
        onClick={() => onNavigate(VIEW_STATES.AGENT_HUB)}
      >
        Agent Hub
      </span>
    );

    // Show Setup if we're past AGENT_HUB
    if (currentView !== VIEW_STATES.AGENT_HUB) {
      items.push(<FontAwesomeIcon key="sep1" icon={faChevronRight} className="separator" />);
      items.push(
        <span 
          key="setup" 
          className={`nav-item ${currentView === VIEW_STATES.SETUP ? 'active' : ''}`}
          onClick={() => onNavigate(VIEW_STATES.SETUP)}
        >
          Setup
        </span>
      );
    }

    // Show Pages List if we're at PAGES_LIST or PAGE_EDITOR
    if (currentView === VIEW_STATES.PAGES_LIST || currentView === VIEW_STATES.PAGE_EDITOR) {
      items.push(<FontAwesomeIcon key="sep2" icon={faChevronRight} className="separator" />);
      items.push(
        <span 
          key="pages" 
          className={`nav-item ${currentView === VIEW_STATES.PAGES_LIST ? 'active' : ''}`}
          onClick={() => onNavigate(VIEW_STATES.PAGES_LIST)}
        >
          {agentName ? `${agentName} Pages` : 'Pages'}
        </span>
      );
    }

    // Show Page Editor if we're at PAGE_EDITOR
    if (currentView === VIEW_STATES.PAGE_EDITOR) {
      items.push(<FontAwesomeIcon key="sep3" icon={faChevronRight} className="separator" />);
      items.push(
        <span key="editor" className="nav-item active">
          {pageName || 'New Page'}
        </span>
      );
    }

    return items;
  };

  return (
    <nav className="template-navigation">
      <div className="breadcrumbs">
        {renderBreadcrumbs()}
      </div>
    </nav>
  );
};

export default TemplateNavigation;