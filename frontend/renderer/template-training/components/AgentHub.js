import React, { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faClock } from '@fortawesome/free-solid-svg-icons';
import WebSocketService from '../../common/services/websocket';
import '../styles/components/AgentHub.scss';

const AgentHub = ({ onSelectAgent, onCreateNew }) => {
  const [agents, setAgents] = useState(() => {
    console.log('🏗️ Initial state construction for agents');
    return [];
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    console.log('🏁 AgentHub component mounted');
    let isComponentMounted = true;  // Add mounted flag
    
    const handleAgentsList = (data) => {
      console.log('📥 Received agents list in component:', data);
      if (!isComponentMounted) {
        console.log('❌ Component unmounted, skipping state update');
        return;
      }
      
      if (data && data.agents) {
        console.log('⚡ About to update agents state:', data.agents);
        setAgents(data.agents);
        setIsLoading(false);
        console.log('👉 Updated agents state with:', data.agents);
      }
    };

    // Set up WebSocket handlers first
    console.log('🔧 Setting up WebSocket handlers');
    const prevHandlers = { ...WebSocketService.stateHandlers };
    console.log('📝 Previous handlers:', Object.keys(prevHandlers));
    
    WebSocketService.setStateHandlers({
      ...prevHandlers,
      onAgentsList: handleAgentsList,
      onConnect: () => {
        console.log('🔌 WebSocket connected, requesting agents list');
        if (isComponentMounted) {
          WebSocketService.getAgents();
        }
      }
    });

    console.log('🔍 Requesting initial agents list');
    setIsLoading(true);
    WebSocketService.getAgents();

    // Cleanup
    return () => {
      console.log('🧹 Cleaning up AgentHub component');
      isComponentMounted = false;
      console.log('🔄 Restoring previous handlers:', Object.keys(prevHandlers));
      WebSocketService.setStateHandlers(prevHandlers);
    };
  }, []);

  // Add render logging
  console.log('🎨 Rendering AgentHub with:', {
    agents,
    isLoading,
    agentsLength: agents.length,
    agentsContent: JSON.stringify(agents)
  });

  return (
    <div className="agent-hub">
      <h2>Agent Hub</h2>
      <div className="agents-grid">
        <div className="agent-card new-agent" onClick={onCreateNew}>
          <FontAwesomeIcon icon={faPlus} className="add-icon" />
          <span>Create New Agent</span>
        </div>

        {isLoading ? (
          <div className="loading-state">Loading agents...</div>
        ) : agents.length === 0 ? (
          <div className="no-agents">No agents found</div>
        ) : (
          agents.map((agent, index) => {
            console.log('🎯 Rendering agent card:', agent);
            return (
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
            );
          })
        )}
      </div>
    </div>
  );
};

export default AgentHub; 