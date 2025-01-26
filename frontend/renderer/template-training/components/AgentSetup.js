import React, { useState } from 'react';
import '../styles/components/AgentSetup.scss';

const AgentSetup = ({ onNext }) => {
  const [agentName, setAgentName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (agentName.trim()) {
      onNext(agentName);
    }
  };

  return (
    <div className="agent-setup">
      <h2>Create New Agent</h2>
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
            disabled
            placeholder="Coming soon..."
          />
        </div>
        <button type="submit" className="primary">
          Continue
        </button>
      </form>
    </div>
  );
};

export default AgentSetup; 