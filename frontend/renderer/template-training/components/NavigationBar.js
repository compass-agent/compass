import React from 'react';
import { VIEW_STATES } from '../constants/viewStates';
import '../styles/components/NavigationBar.scss';

const NavigationBar = ({ currentView, agentName }) => {
  return (
    <div className="navigation-bar">
      <div className="nav-title">
        {currentView === VIEW_STATES.SETUP ? (
          'Create New Agent'
        ) : (
          <>Agent: {agentName}</>
        )}
      </div>
      <div className="nav-steps">
        {currentView !== VIEW_STATES.SETUP && (
          <span className="step-indicator">
            {currentView === VIEW_STATES.PAGES_LIST ? 'Pages List' : 'Page Editor'}
          </span>
        )}
      </div>
    </div>
  );
};

export default NavigationBar; 