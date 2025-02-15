import React, { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faClock } from '@fortawesome/free-solid-svg-icons';
import WebSocketService from '../../common/services/websocket';
import '../styles/components/AgentHub.scss';

const AgentHub = ({ onSelectAgent, onCreateNew }) => {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    let isComponentMounted = true;
    
    const handleAgentsList = (data) => {
      if (!isComponentMounted) return;
      if (data && data.agents) {
        setAgents(data.agents);
      }
    };

    const handleConnect = () => {
      if (isComponentMounted) {
        WebSocketService.getAgents();
      }
    };

    // Add handlers
    WebSocketService.addHandler('onAgentsList', handleAgentsList);
    WebSocketService.addHandler('onConnect', handleConnect);

    // Get initial agents list
    WebSocketService.getAgents();

    return () => {
      isComponentMounted = false;
      // Remove handlers on cleanup
      WebSocketService.removeHandler('onAgentsList', handleAgentsList);
      WebSocketService.removeHandler('onConnect', handleConnect);
    };
  }, []);

  return (
    <div className="agent-hub">
      <h2>Agent Hub</h2>
      <div className="agents-grid">
        {agents.length === 0 ? (
          <div className="no-agents">No agents found</div>
        ) : (
          agents.map((agent) => (
            <div 
              key={agent.name}
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
          ))
        )}
        
        <div className="agent-card new-agent" onClick={onCreateNew}>
          <FontAwesomeIcon icon={faPlus} className="add-icon" />
          <span>Create New Agent</span>
        </div>
      </div>
    </div>
  );
};

export default AgentHub; 