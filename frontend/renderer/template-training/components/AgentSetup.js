import React, { useState } from 'react';
import '../styles/components/AgentSetup.scss';

const AgentSetup = ({ onNext }) => {
  const [agentName, setAgentName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (agentName.trim()) {
      onNext(agentName);
    }
  };

  const handleDocumentationClick = () => {
    // TODO: Implement documentation page navigation
    console.log('Documentation button clicked - feature coming soon');
  };

  return (
    <div className="agent-setup">
      <h2>Agent Setup</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="agentName">Agent Name</label>
          <input
            id="agentName"
            type="text"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            placeholder="Enter agent name"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter a short description of what this agent does"
            rows={4}
          />
        </div>
        <div className="button-group">
          <button 
            type="button" 
            className="secondary"
            onClick={handleDocumentationClick}
          >
            Add Documentation
          </button>
          <button type="submit" className="primary">
            Add Pages
          </button>
        </div>
      </form>
    </div>
  );
};

export default AgentSetup; 