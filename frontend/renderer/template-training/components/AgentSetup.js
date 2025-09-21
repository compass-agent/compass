import { faInfoCircle, faPlus, faTrash, faPen, faEllipsisV } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useState } from "react"
import "../styles/components/AgentSetup.scss"

// Available software options
const AVAILABLE_SOFTWARE = [
  { id: 'SAP2000', name: 'SAP2000' },
  { id: 'ETABS', name: 'ETABS' },
  { id: 'AutoCAD', name: 'AutoCAD' },
  { id: 'FreeCAD', name: 'FreeCAD' },
  { id: 'Ansys', name: 'Ansys' }
]

// Available general tools
const AVAILABLE_TOOLS = [
  { id: 'commandLine', name: 'Command Line', description: 'Execute command line operations' },
  { id: 'fileEditor', name: 'File Editor', description: 'Access and edit project files' }
]

// Toggle Switch component with inline styles
const ToggleSwitch = ({ checked, onChange, disabled = false }) => {
  const toggleStyles = {
    position: 'relative',
    display: 'inline-block',
    width: '44px',
    height: '24px',
    opacity: disabled ? 0.5 : 1,
    pointerEvents: disabled ? 'none' : 'auto'
  }

  const inputStyles = {
    opacity: 0,
    width: 0,
    height: 0
  }

  const sliderStyles = {
    position: 'absolute',
    cursor: 'pointer',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: checked ? '#9E61CA' : '#404040',
    transition: 'all 0.3s ease',
    borderRadius: '24px'
  }

  const knobStyles = {
    position: 'absolute',
    content: '""',
    height: '18px',
    width: '18px',
    left: '3px',
    bottom: '3px',
    backgroundColor: '#ffffff',
    transition: 'all 0.3s ease',
    borderRadius: '50%',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
    transform: checked ? 'translateX(20px)' : 'translateX(0px)'
  }

  const handleToggle = (e) => {
    e.stopPropagation()
    if (!disabled && onChange) {
      onChange({ target: { checked: !checked } })
    }
  }

  return (
    <div style={toggleStyles} onClick={handleToggle}>
      <input
        type="checkbox"
        checked={checked}
        onChange={handleToggle}
        disabled={disabled}
        style={inputStyles}
      />
      <span style={sliderStyles}>
        <span style={knobStyles}></span>
      </span>
    </div>
  )
}

// Tooltip component with free positioning
const Tooltip = ({ text, children }) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })

  const handleMouseEnter = (e) => {
    const rect = e.target.getBoundingClientRect()
    setPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    })
    setShowTooltip(true)
  }

  const handleMouseLeave = () => {
    setShowTooltip(false)
  }

  return (
    <>
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{ display: 'inline-block' }}
      >
        {children}
      </div>
      {showTooltip && (
        <div
          style={{
            position: 'fixed',
            left: position.x,
            top: position.y,
            transform: 'translateX(-50%) translateY(-100%)',
            backgroundColor: '#4A4A4A',
            color: '#E0E0E0',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            lineHeight: '1.4',
            whiteSpace: 'normal',
            maxWidth: '280px',
            width: 'max-content',
            zIndex: 999999,
            border: '1px solid #666',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
            pointerEvents: 'none'
          }}
        >
          {text}
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 0,
              height: 0,
              borderLeft: '5px solid transparent',
              borderRight: '5px solid transparent',
              borderTop: '5px solid #4A4A4A'
            }}
          />
        </div>
      )}
    </>
  )
}

// Configuration Modal component
const ConfigModal = ({ type, data, onSave, onClose }) => {
  const [formData, setFormData] = useState(data)

  const handleSave = () => {
    onSave(formData)
  }

  // Check if at least one capability is selected for software configuration
  const isValidConfiguration = () => {
    if (type === 'software') {
      return formData.scripting || formData.desktop
    }
    return true // For other types, always valid
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{data.isNew ? 'Configure' : 'Edit'} {data.name}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        {/* SAP2000 explanation */}
        {type === 'software' && data.id === 'SAP2000' && (
          <div style={{
            padding: '1rem 1.5rem 0',
            borderBottom: '1px solid #404040',
            backgroundColor: '#2c2c2c'
          }}>
            <p style={{
              margin: 0,
              color: '#b0b0b0',
              fontSize: '0.9rem',
              lineHeight: '1.4',
              paddingBottom: '1rem'
            }}>
              SAP2000 is a structural analysis and design software that the agent can use to perform engineering calculations, create models, run analyses, and generate reports.
            </p>
          </div>
        )}
        
        <div className="modal-body">
          {type === 'tool' && data.id === 'fileEditor' && (
            <>
              <div className="form-group">
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem'}}>
                  <label style={{margin: 0, color: '#ffffff', fontWeight: 500}}>Root Directory</label>
                  <Tooltip text="The base directory path that the agent can access. Agent will be able to read and edit files within this directory and its subdirectories.">
                    <FontAwesomeIcon 
                      icon={faInfoCircle} 
                      style={{color: '#a0a0a0', cursor: 'help', fontSize: '0.85rem'}}
                    />
                  </Tooltip>
                </div>
                <input
                  type="text"
                  value={formData.config.rootDir}
                  onChange={(e) => setFormData({
                    ...formData,
                    config: { ...formData.config, rootDir: e.target.value }
                  })}
                  placeholder="e.g., C:\Projects\"
                />
              </div>
              <div className="form-group">
                <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                  <ToggleSwitch
                    checked={formData.config.restricted}
                    onChange={(e) => setFormData({
                      ...formData,
                      config: { ...formData.config, restricted: e.target.checked }
                    })}
                  />
                  <span style={{color: '#e0e0e0', fontSize: '0.9rem', fontWeight: 400, margin: 0}}>
                    Restrict to subdirectories only
                  </span>
                </div>
              </div>
            </>
          )}
          
          {type === 'software' && (
            <>
              <div style={{width: '100%'}}>
                {/* Scripting Configuration Box */}
                <div style={{
                  backgroundColor: '#2a2a2a',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  marginBottom: '1.5rem',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    padding: '1rem 1.25rem',
                    backgroundColor: '#333333',
                    borderBottom: '1px solid #404040'
                  }}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                      <ToggleSwitch
                        checked={formData.scripting}
                        onChange={(e) => setFormData({
                          ...formData,
                          scripting: e.target.checked
                        })}
                      />
                      <span style={{color: '#ffffff', fontWeight: 500, fontSize: '0.95rem', margin: 0}}>
                        Scripting
                      </span>
                      <Tooltip text="Agent can interact with this software through its API and scripting interfaces (COM, REST API, etc.). This includes programmatic control, data exchange, and automated operations through the software's built-in scripting capabilities.">
                        <FontAwesomeIcon 
                          icon={faInfoCircle} 
                          style={{color: '#a0a0a0', cursor: 'help', fontSize: '0.85rem'}}
                        />
                      </Tooltip>
                    </div>
                    <div style={{
                      padding: '0.5rem 1.25rem 0',
                      color: '#b0b0b0',
                      fontSize: '0.8rem',
                      lineHeight: '1.4'
                    }}>
                      Allows the agent to control the software programmatically through APIs and scripting. 
                      This enables automated operations, data processing, and integration with other systems.
                    </div>
                  </div>
                  
                  {formData.scripting && (
                    <div style={{padding: '1.25rem'}}>
                      {data.id === 'SAP2000' && (
                        <>
                          <div style={{marginBottom: '1.25rem'}}>
                            <label style={{
                              display: 'flex',
                              alignItems: 'center',
                              color: '#e0e0e0',
                              fontSize: '0.9rem',
                              fontWeight: 400,
                              marginBottom: '0.5rem',
                              cursor: 'pointer'
                            }}>
                              <input
                                type="checkbox"
                                checked={formData.config.sapAutoAttach || false}
                                onChange={(e) => setFormData({
                                  ...formData,
                                  config: { ...formData.config, sapAutoAttach: e.target.checked }
                                })}
                                style={{marginRight: '0.75rem', accentColor: '#9E61CA', transform: 'scale(1.1)'}}
                              />
                              SAP end-to-end configuration attached
                            </label>
                          </div>
                          <div style={{marginBottom: 0}}>
                            <label style={{
                              display: 'block',
                              marginBottom: '0.75rem',
                              fontWeight: 500,
                              color: '#ffffff'
                            }}>
                              SAP2000 Version
                            </label>
                            <select
                              value={formData.config.sapApiVersion || 'v24'}
                              onChange={(e) => setFormData({
                                ...formData,
                                config: { ...formData.config, sapApiVersion: e.target.value }
                              })}
                              style={{
                                width: '100%',
                                maxWidth: '250px',
                                padding: '0.75rem',
                                backgroundColor: '#1e1e1e',
                                border: '1px solid #505050',
                                borderRadius: '6px',
                                color: '#e0e0e0',
                                fontSize: '0.9rem'
                              }}
                            >
                              <option value="v24">SAP2000 v24</option>
                              <option value="v23">SAP2000 v23</option>
                              <option value="v22">SAP2000 v22</option>
                            </select>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Desktop Control Configuration Box */}
                <div style={{
                  backgroundColor: '#2a2a2a',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  marginBottom: 0,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    padding: '1rem 1.25rem',
                    backgroundColor: '#333333',
                    borderBottom: '1px solid #404040'
                  }}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                      <ToggleSwitch
                        checked={formData.desktop}
                        onChange={(e) => setFormData({
                          ...formData,
                          desktop: e.target.checked
                        })}
                      />
                      <span style={{color: '#ffffff', fontWeight: 500, fontSize: '0.95rem', margin: 0}}>
                        Desktop Control
                      </span>
                      <Tooltip text="Agent can interact with this software through its desktop interface using UI automation. This includes clicking buttons, entering text, reading screen content, and navigating menus just like a human user would.">
                        <FontAwesomeIcon 
                          icon={faInfoCircle} 
                          style={{color: '#a0a0a0', cursor: 'help', fontSize: '0.85rem'}}
                        />
                      </Tooltip>
                    </div>
                    <div style={{
                      padding: '0.5rem 1.25rem 0',
                      color: '#b0b0b0',
                      fontSize: '0.8rem',
                      lineHeight: '1.4'
                    }}>
                      Enables the agent to interact with the software's user interface like a human user. 
                      This includes clicking, typing, reading screen content, and navigating through menus and dialogs.
                    </div>
                  </div>
                  
                  {formData.desktop && (
                    <div style={{padding: '1.25rem'}}>
                      <div style={{marginBottom: 0}}>
                        <label style={{
                          display: 'flex',
                          alignItems: 'center',
                          color: '#e0e0e0',
                          fontSize: '0.9rem',
                          fontWeight: 400,
                          marginBottom: '0.5rem',
                          cursor: 'pointer'
                        }}>
                          <input
                            type="checkbox"
                            checked={formData.config.restrictedToSoftware || false}
                            onChange={(e) => setFormData({
                              ...formData,
                              config: { ...formData.config, restrictedToSoftware: e.target.checked }
                            })}
                            style={{marginRight: '0.75rem', accentColor: '#9E61CA', transform: 'scale(1.1)'}}
                          />
                          Restrict to only this software's UI
                        </label>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
        
        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button 
            type="button" 
            className="btn-primary" 
            onClick={handleSave}
            disabled={!isValidConfiguration()}
          >
            {data.isNew ? 'Add' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

const AgentSetup = ({ onNext, onTrainUI, existingAgent }) => {
  const [agentName, setAgentName] = useState("")
  const [description, setDescription] = useState("")
  const [prompt, setPrompt] = useState("")
  const [generalTools, setGeneralTools] = useState([])
  const [softwareIntegrations, setSoftwareIntegrations] = useState([])
  const [showAddToolDropdown, setShowAddToolDropdown] = useState(false)
  const [showAddSoftwareDropdown, setShowAddSoftwareDropdown] = useState(false)
  
  // Modal states
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [configModalData, setConfigModalData] = useState(null)
  const [configModalType, setConfigModalType] = useState(null) // 'tool' or 'software'
  
  // Dropdown menu states
  const [activeDropdown, setActiveDropdown] = useState(null)

  useEffect(() => {
    if (existingAgent && existingAgent.name) {
      // Populate all fields with existing agent data
      setAgentName(existingAgent.name || "")
      setDescription(existingAgent.description || "")
      setPrompt(existingAgent.prompt || "")
      
      // Use new data structure directly
      setGeneralTools(existingAgent.generalTools || [])
      setSoftwareIntegrations(existingAgent.softwareIntegrations || [])
    } else {
      // Reset form for new agent
      setAgentName("")
      setDescription("")
      setPrompt("")
      setGeneralTools([])
      setSoftwareIntegrations([])
    }
  }, [existingAgent])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.actions-dropdown')) {
        setActiveDropdown(null)
      }
      if (!event.target.closest('.add-button-container')) {
        setShowAddToolDropdown(false)
        setShowAddSoftwareDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Handler functions for general tools
  const addGeneralTool = (toolId) => {
    const tool = AVAILABLE_TOOLS.find(t => t.id === toolId)
    if (tool && !generalTools.find(t => t.id === toolId)) {
      setShowAddToolDropdown(false)
      
      if (tool.id === 'fileEditor') {
        // Show configuration modal for File Editor
        setConfigModalType('tool')
        setConfigModalData({
          id: tool.id,
          name: tool.name,
          config: { rootDir: '', restricted: true },
          isNew: true
        })
        setShowConfigModal(true)
      } else {
        // Add tool directly for others
        const newTool = {
          id: tool.id,
          name: tool.name,
          config: { access: 'full' }
        }
        setGeneralTools([...generalTools, newTool])
      }
    }
  }

  const removeGeneralTool = (toolId) => {
    setGeneralTools(generalTools.filter(t => t.id !== toolId))
    setActiveDropdown(null)
  }

  const editGeneralTool = (toolId) => {
    const tool = generalTools.find(t => t.id === toolId)
    if (tool) {
      setConfigModalType('tool')
      setConfigModalData({
        ...tool,
        isNew: false
      })
      setShowConfigModal(true)
      setActiveDropdown(null)
    }
  }

  // Handler functions for software integrations
  const addSoftwareIntegration = (softwareId) => {
    const software = AVAILABLE_SOFTWARE.find(s => s.id === softwareId)
    if (software && !softwareIntegrations.find(s => s.id === softwareId)) {
      setShowAddSoftwareDropdown(false)
      
      // Show configuration modal for software
      setConfigModalType('software')
      setConfigModalData({
        id: software.id,
        name: software.name,
        scripting: false,
        desktop: false,
        config: {},
        trainingStatus: 'not_configured',
        isNew: true
      })
      setShowConfigModal(true)
    }
  }

  const removeSoftwareIntegration = (softwareId) => {
    setSoftwareIntegrations(softwareIntegrations.filter(s => s.id !== softwareId))
    setActiveDropdown(null)
  }

  const editSoftwareIntegration = (softwareId) => {
    const software = softwareIntegrations.find(s => s.id === softwareId)
    if (software) {
      setConfigModalType('software')
      setConfigModalData({
        ...software,
        isNew: false
      })
      setShowConfigModal(true)
      setActiveDropdown(null)
    }
  }

  // Modal handlers
  const handleModalSave = (updatedData) => {
    if (configModalType === 'tool') {
      if (updatedData.isNew) {
        setGeneralTools([...generalTools, updatedData])
      } else {
        setGeneralTools(generalTools.map(t => 
          t.id === updatedData.id ? updatedData : t
        ))
      }
    } else if (configModalType === 'software') {
      if (updatedData.isNew) {
        setSoftwareIntegrations([...softwareIntegrations, updatedData])
      } else {
        setSoftwareIntegrations(softwareIntegrations.map(s => 
          s.id === updatedData.id ? updatedData : s
        ))
      }
    }
    setShowConfigModal(false)
    setConfigModalData(null)
    setConfigModalType(null)
  }

  const handleModalClose = () => {
    setShowConfigModal(false)
    setConfigModalData(null)
    setConfigModalType(null)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (agentName.trim()) {
      // Use new format - no need to convert back to old format
      // The backend now supports the new structure
      const agentData = {
        name: agentName,
        description,
        prompt,
        generalTools,
        softwareIntegrations,
        configuration: {}
      }
      onNext(agentData)
    }
  }

  return (
    <div className="agent-setup">
      <form onSubmit={handleSubmit}>
        {/* Core Identity Section */}
        <div className="form-group">
          <label htmlFor="agentName">Name</label>
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
            placeholder="Enter aaaa short description of what this agent does"
            rows={3}
          />
        </div>

        <div className="form-group">
          <label htmlFor="prompt">Core Prompt</label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter the main instructions that define the agent's behavior and capabilities"
            rows={4}
          />
        </div>

        {/* General Tools Section */}
        <div className="form-group">
          <div className="section-header">
            <label>General Tools</label>
            <div className="add-button-container">
              <button
                type="button"
                className="btn-secondary add-button"
                onClick={() => setShowAddToolDropdown(!showAddToolDropdown)}
              >
                <FontAwesomeIcon icon={faPlus} /> Add Tool
              </button>
              {showAddToolDropdown && (
                <div className="dropdown-menu">
                  {AVAILABLE_TOOLS.filter(tool => !generalTools.find(t => t.id === tool.id)).map(tool => (
                    <div key={tool.id} className="dropdown-item" onClick={() => addGeneralTool(tool.id)}>
                      {tool.name}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          <div className="tools-table">
            {generalTools.length === 0 ? (
              <div className="empty-state">No general tools added</div>
            ) : (
              <>
                <div className="table-header">
                  <div className="col tool-name">Tool</div>
                  <div className="col configuration">Configuration</div>
                  <div className="col actions">Actions</div>
                </div>
                <div className="table-body">
                  {generalTools.map(tool => (
                    <div key={tool.id} className="table-row">
                      <div className="col tool-name">{tool.name}</div>
                      <div className="col configuration">
                        {tool.id === 'fileEditor' ? 
                          `Root: ${tool.config.rootDir || 'Not set'}, ${tool.config.restricted ? 'Restricted' : 'Full access'}` :
                          `${tool.config.access === 'full' ? 'Full system access' : 'Restricted access'}`
                        }
                      </div>
                      <div className="col actions">
                        <div className="actions-dropdown">
                          <button
                            type="button"
                            className="icon-btn three-dots"
                            onClick={() => setActiveDropdown(activeDropdown === `tool-${tool.id}` ? null : `tool-${tool.id}`)}
                          >
                            <FontAwesomeIcon icon={faEllipsisV} />
                          </button>
                          {activeDropdown === `tool-${tool.id}` && (
                            <div className="dropdown-menu">
                              <div className="dropdown-item" onClick={() => editGeneralTool(tool.id)}>
                                <FontAwesomeIcon icon={faPen} />
                                <span>Edit</span>
                              </div>
                              <div className="dropdown-item danger" onClick={() => removeGeneralTool(tool.id)}>
                                <FontAwesomeIcon icon={faTrash} />
                                <span>Delete</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Software Integrations Section */}
        <div className="form-group">
          <div className="section-header">
            <label>Software Integrations</label>
            <div className="add-button-container">
            <button
              type="button"
                className="btn-secondary add-button"
                onClick={() => setShowAddSoftwareDropdown(!showAddSoftwareDropdown)}
              >
                <FontAwesomeIcon icon={faPlus} /> Add Software
            </button>
              {showAddSoftwareDropdown && (
                <div className="dropdown-menu">
                  {AVAILABLE_SOFTWARE.filter(software => !softwareIntegrations.find(s => s.id === software.id)).map(software => (
                    <div key={software.id} className="dropdown-item" onClick={() => addSoftwareIntegration(software.id)}>
                      {software.name}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          <div className="software-table">
            {softwareIntegrations.length === 0 ? (
              <div className="empty-state">No software integrations added</div>
            ) : (
              <>
                <div className="table-header">
                  <div className="col software-name">Software</div>
                  <div className="col configuration">Configuration</div>
                  <div className="col actions">Actions</div>
                </div>
                <div className="table-body">
                  {softwareIntegrations.map(software => (
                    <div key={software.id} className="table-row">
                      <div className="col software-name">{software.name}</div>
                      <div className="col configuration">
                        <div className="config-status">
                          {software.scripting && <span className="config-badge">Scripting</span>}
                          {software.desktop && <span className="config-badge">Desktop</span>}
                          {software.desktop && (
                            <button
                              type="button"
                              className="btn-secondary train-ui-btn"
                              onClick={() => {
                                const agentData = {
                                  name: agentName,
                                  description,
                                  prompt,
                                  generalTools,
                                  softwareIntegrations
                                }
                                if (onTrainUI) {
                                  onTrainUI(agentData)
                                }
                              }}
                              style={{
                                marginLeft: '0.5rem',
                                padding: '0.25rem 0.5rem',
                                fontSize: '0.75rem',
                                borderRadius: '4px'
                              }}
                            >
                              Train UI
                            </button>
                          )}
                        </div>
        </div>
                      <div className="col actions">
                        <div className="actions-dropdown">
                          <button
                            type="button"
                            className="icon-btn three-dots"
                            onClick={() => setActiveDropdown(activeDropdown === `software-${software.id}` ? null : `software-${software.id}`)}
                          >
                            <FontAwesomeIcon icon={faEllipsisV} />
                          </button>
                          {activeDropdown === `software-${software.id}` && (
                            <div className="dropdown-menu">
                              <div className="dropdown-item" onClick={() => editSoftwareIntegration(software.id)}>
                                <FontAwesomeIcon icon={faPen} />
                                <span>Edit</span>
                              </div>
                              <div className="dropdown-item danger" onClick={() => removeSoftwareIntegration(software.id)}>
                                <FontAwesomeIcon icon={faTrash} />
                                <span>Delete</span>
            </div>
            </div>
                          )}
            </div>
          </div>
        </div>
                  ))}
            </div>
              </>
            )}
          </div>
        </div>

        <div className="button-group">
          <button type="submit" className="primary create-agent-btn">
            {existingAgent ? "Save Changes" : "Create Agent"}
          </button>
        </div>
      </form>

      {/* Configuration Modal */}
      {showConfigModal && configModalData && (
        <ConfigModal
          type={configModalType}
          data={configModalData}
          onSave={handleModalSave}
          onClose={handleModalClose}
        />
      )}
    </div>
  )
}

export default AgentSetup
