import React, { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faClock } from '@fortawesome/free-solid-svg-icons';
import WebSocketService from '../../common/services/websocket';
import '../styles/components/AgentHub.scss';

const AgentHub = ({ onSelectAgent, onCreateNew }) => {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    console.log('🏁 AgentHub component mounted');
    
    const handleAgentsList = (data) => {
      console.log('📥 Received agents list in component:', data);
      if (data && data.agents) {
        setAgents(data.agents);
        console.log('👉 Updated agents state with:', data.agents);
      }
    };

    const handleConnect = () => {
      console.log('🔌 WebSocket connected, requesting agents list');
      WebSocketService.getAgents();
    };

    // Set up WebSocket handlers
    console.log('🔧 Setting up WebSocket handlers');
    WebSocketService.setStateHandlers({
      ...WebSocketService.stateHandlers,
      onAgentsList: handleAgentsList,
      onConnect: handleConnect
    });

    // If socket is already connected, request agents immediately
    if (WebSocketService.socket?.connected) {
      console.log('🔍 Socket already connected, requesting agents list');
      WebSocketService.getAgents();
    }

    // Cleanup
    return () => {
      console.log('🧹 Cleaning up AgentHub component');
      WebSocketService.setStateHandlers({
        ...WebSocketService.stateHandlers,
        onAgentsList: null,
        onConnect: null
      });
    };
  }, []);

  console.log('🎨 Rendering AgentHub with agents:', agents);

  return (
    <div className="agent-hub">
      <h2>Agent Hub</h2>
      <div className="agents-grid">
        {/* Create New Agent Card */}
        <div className="agent-card new-agent" onClick={onCreateNew}>
          <FontAwesomeIcon icon={faPlus} className="add-icon" />
          <span>Create New Agent</span>
        </div>

        {/* Existing Agents */}
        {agents && agents.map((agent, index) => (
          <div 
            key={index}
            className="agent-card"
            onClick={() => onSelectAgent(agent.name)}
          >
            <div className="agent-info">
              <h3>{agent.name || 'Unnamed Agent'}</h3>
              <div className="last-modified">
                <FontAwesomeIcon icon={faClock} />
                <span>
                  {agent.last_modified 
                    ? new Date(agent.last_modified).toLocaleDateString()
                    : 'No date'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentHub; 