import {
  faCheckCircle,
  faCircle,
  faExclamationCircle,
  faInfoCircle,
  faTimes,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import jsyaml from "js-yaml"
import React, { useEffect, useState } from "react"
import WebSocketService from "../../common/services/websocket"
import "../styles/InitSapConfig.scss"

const Tooltip = ({ text, children }) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  const handleMouseEnter = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setPosition({
      top: rect.top - 10, // Position above the icon
      left: rect.right + 5, // Position to the right of the icon
    })
    setShowTooltip(true)
  }

  const handleMouseLeave = () => {
    setShowTooltip(false)
  }

  return (
    <div className="tooltip-container">
      <div onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
        {children}
      </div>
      {showTooltip && (
        <div
          className="tooltip-content-fixed"
          style={{
            top: position.top,
            left: position.left,
          }}
        >
          {text}
        </div>
      )}
    </div>
  )
}

const InitSapConfig = ({ isOpen, onClose, onSubmit }) => {
  const [currentStep, setCurrentStep] = useState(1)

  // Check if this is an edit (has been submitted before)
  const isEdit = localStorage.getItem("sapConfigSubmitted") === "true"

  // Tooltip information for each field
  const tooltipInfo = {
    units: "Unit system to use in SAP2000 (kip-in, kip-ft, N-mm, N-m, etc.)",
    modelPath: "Where to save the model files",
    defaultMaterial:
      "Default steel material for sections. Material properties can be expanded as needed.",
    baseRestraints:
      "Base restraints for columns [UX, UY, UZ, RX, RY, RZ]. true = restrained, false = free",
    autoDetectColumns:
      "Automatic detection of ground level columns. This currently must be true!",
    loadPatterns: "Load patterns to create and use in the analysis",
    floorDeadLoad: "Regular floor dead loads in PSF (pounds per square foot)",
    floorLiveLoad: "Regular floor live loads in PSF (pounds per square foot)",
    roofDeadLoad: "Roof dead loads in PSF (pounds per square foot)",
    roofLiveLoad: "Roof live loads in PSF (pounds per square foot)",
    loadDirectionType:
      "Load direction type. GLOBAL_Z: Loads in global Z direction. DECK_ORIENTED: Loads aligned with the deck direction (determined by shortest edge)",
    exclusionAreas:
      "Areas to exclude from load application. Define specific regions that should not receive area loads, such as openings for elevators, stairs, mechanical shafts, etc. Format: [x, y, z] coordinates. Use null to match any value.",
    sectionTypes:
      "Types of sections to consider for design. W: Wide flange sections, HSS: Hollow Structural Sections, PIPE: Circular hollow sections, L: Angle sections, WT: Structural tees, C: Channel sections, MC: Miscellaneous channel sections",
    depthRange:
      "Depth range (inches) - controls the minimum and maximum depth of sections to consider. This helps exclude sections that are too small to be practical or too deep for the available space",
    weightRange:
      "Weight range (lbs/ft) - controls the weight per unit length of sections to consider. This helps exclude extremely light or heavy sections that would be impractical",
    designCode:
      "Design code to use for checking member capacity. This is the structural steel design specification that will be used",
    maxUsageRatio:
      "Maximum allowed usage ratio (0.0 to 1.0). This is the maximum percentage of a member's capacity that you'll allow. Example: 0.9 means members can be loaded up to 90% of their capacity",
    weightMinimization:
      "How important is minimizing the overall weight of the structure? Higher value = program will work harder to find the lightest possible structure",
    connectionCompatibility:
      "How important is making sure connected members have similar depths? Higher value = program will try to match depths at connections for easier detailing",
    floorConsistency:
      "How important is using the same section types throughout a floor? Higher value = program will try to use fewer different sections on each floor",
    maxGroups:
      "Maximum number of different section sizes to use in the building. Lower number = fewer different sections to detail and fabricate",
    beamColumnSegregation:
      "Should beams and columns always use different section types? true = beams and columns will never share the same section",
    groupByFloor:
      "Should sections be consistent within each floor level? true = program will try to use the same sections for similar members on each floor",
  }

  // Helper function to create label with tooltip
  const LabelWithTooltip = ({ htmlFor, text, tooltipKey, className = "" }) => (
    <label htmlFor={htmlFor} className={className}>
      {text}
      {tooltipInfo[tooltipKey] && (
        <Tooltip text={tooltipInfo[tooltipKey]}>
          <FontAwesomeIcon icon={faInfoCircle} className="tooltip-icon" />
        </Tooltip>
      )}
    </label>
  )

  const [formState, setFormState] = useState({
    // Step 1: General & Materials
    units: "kip-in",
    defaultMaterial: "A992Fy50",

    // Step 2: Restraints & Loads
    baseRestraints: {
      UX: true,
      UY: true,
      UZ: true,
      RX: false,
      RY: false,
      RZ: false,
    },
    autoDetectColumns: true,
    loadPatterns: "DEAD, LIVE",
    loadDirectionType: "DECK_ORIENTED",
    floorDeadLoad: 50.0,
    floorLiveLoad: 50.0,
    roofDeadLoad: 20.0,
    roofLiveLoad: 20.0,
    exclusionAreas: [
      { x: 12.5, y: 20.0, z: null },
      { x: 30.0, y: 15.0, z: 14.0 },
    ],

    // Step 3: Section Candidates & Design
    sectionTypes: ["W"],
    depthRangeMin: 6,
    depthRangeMax: 26,
    weightRangeMin: 10,
    weightRangeMax: 360,
    designCode: "AISC 360-16",
    maxUsageRatio: 0.9,
    weightMinimization: 1.0,
    connectionCompatibility: 0.5,
    floorConsistency: 0.3,
    maxGroups: 8,
    beamColumnSegregation: true,
    groupByFloor: true,
  })

  const [fieldErrors, setFieldErrors] = useState({})
  const [stepStatus, setStepStatus] = useState({
    1: "incomplete",
    2: "incomplete",
    3: "incomplete",
    4: "incomplete",
  })

  // Validate each step and update status
  useEffect(() => {
    // Step 1 validation (General Settings only)
    const step1Errors = {}
    if (!formState.units) step1Errors.units = "Required"
    if (!formState.defaultMaterial) step1Errors.defaultMaterial = "Required"

    // Step 2 validation (Restraints + Load Definitions)
    const step2Errors = {}
    if (!formState.loadPatterns) step2Errors.loadPatterns = "Required"
    if (formState.floorDeadLoad === "" || formState.floorDeadLoad === null)
      step2Errors.floorDeadLoad = "Required"
    if (formState.floorLiveLoad === "" || formState.floorLiveLoad === null)
      step2Errors.floorLiveLoad = "Required"
    if (formState.roofDeadLoad === "" || formState.roofDeadLoad === null)
      step2Errors.roofDeadLoad = "Required"
    if (formState.roofLiveLoad === "" || formState.roofLiveLoad === null)
      step2Errors.roofLiveLoad = "Required"

    // Step 3 validation (Section Candidates only)
    const step3Errors = {}
    if (formState.sectionTypes.length === 0)
      step3Errors.sectionTypes = "Required"
    if (formState.depthRangeMin === "" || formState.depthRangeMin === null)
      step3Errors.depthRangeMin = "Required"
    if (formState.depthRangeMax === "" || formState.depthRangeMax === null)
      step3Errors.depthRangeMax = "Required"
    if (formState.weightRangeMin === "" || formState.weightRangeMin === null)
      step3Errors.weightRangeMin = "Required"
    if (formState.weightRangeMax === "" || formState.weightRangeMax === null)
      step3Errors.weightRangeMax = "Required"

    // Step 4 validation (Design Optimization)
    const step4Errors = {}
    if (!formState.designCode) step4Errors.designCode = "Required"
    if (formState.maxUsageRatio === "" || formState.maxUsageRatio === null)
      step4Errors.maxUsageRatio = "Required"
    if (
      formState.weightMinimization === "" ||
      formState.weightMinimization === null
    )
      step4Errors.weightMinimization = "Required"
    if (
      formState.connectionCompatibility === "" ||
      formState.connectionCompatibility === null
    )
      step4Errors.connectionCompatibility = "Required"
    if (
      formState.floorConsistency === "" ||
      formState.floorConsistency === null
    )
      step4Errors.floorConsistency = "Required"
    if (formState.maxGroups === "" || formState.maxGroups === null)
      step4Errors.maxGroups = "Required"

    // Update errors state
    setFieldErrors({
      ...step1Errors,
      ...step2Errors,
      ...step3Errors,
      ...step4Errors,
    })

    // Update step status
    setStepStatus({
      1: Object.keys(step1Errors).length > 0 ? "error" : "complete",
      2: Object.keys(step2Errors).length > 0 ? "error" : "complete",
      3: Object.keys(step3Errors).length > 0 ? "error" : "complete",
      4: Object.keys(step4Errors).length > 0 ? "error" : "complete",
    })
  }, [formState])

  // Check if all steps are complete for submit button
  const isFormComplete = Object.values(stepStatus).every(
    (status) => status === "complete"
  )

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target

    if (type === "checkbox") {
      if (name.startsWith("baseRestraint_")) {
        const restraintKey = name.replace("baseRestraint_", "")
        setFormState((prev) => ({
          ...prev,
          baseRestraints: {
            ...prev.baseRestraints,
            [restraintKey]: checked,
          },
        }))
      } else {
        setFormState((prev) => ({
          ...prev,
          [name]: checked,
        }))
      }
    } else if (type === "number") {
      setFormState((prev) => ({
        ...prev,
        [name]: value === "" ? "" : parseFloat(value),
      }))
    } else {
      setFormState((prev) => ({
        ...prev,
        [name]: value,
      }))
    }
  }

  const handleExclusionAreaChange = (index, field, value) => {
    setFormState((prev) => {
      const updatedAreas = [...prev.exclusionAreas]
      let processedValue

      if (value === "" || value === "null" || value === null) {
        processedValue = null
      } else {
        const numValue = parseFloat(value)
        processedValue = isNaN(numValue) ? value : numValue
      }

      updatedAreas[index] = {
        ...updatedAreas[index],
        [field]: processedValue,
      }
      return {
        ...prev,
        exclusionAreas: updatedAreas,
      }
    })
  }

  const addExclusionArea = () => {
    setFormState((prev) => ({
      ...prev,
      exclusionAreas: [...prev.exclusionAreas, { x: "", y: "", z: null }],
    }))
  }

  const removeExclusionArea = (index) => {
    setFormState((prev) => ({
      ...prev,
      exclusionAreas: prev.exclusionAreas.filter((_, i) => i !== index),
    }))
  }

  const handleSectionTypeChange = (type) => {
    setFormState((prev) => {
      const updatedTypes = prev.sectionTypes.includes(type)
        ? prev.sectionTypes.filter((t) => t !== type)
        : [...prev.sectionTypes, type]

      return {
        ...prev,
        sectionTypes: updatedTypes,
      }
    })
  }

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const goToStep = (step) => {
    if (step >= 1 && step <= 4) {
      setCurrentStep(step)
    }
  }

  // Resolve the user-facing workspace directory (Documents/Compass in
  // production; the repo root in development). Falls back to relative paths
  // if the preload API is unavailable.
  const getWorkspacePaths = async () => {
    try {
      const paths = await window.electron?.settings?.getPaths()
      if (paths?.workspaceDir) {
        return {
          modelsDir: paths.modelsDir || `${paths.workspaceDir}/models`,
          configFile:
            paths.sapConfigPath ||
            `${paths.workspaceDir}/models/.sapConfig.yml`,
        }
      }
    } catch (_) {
      /* fall through to relative paths */
    }
    return { modelsDir: "./models", configFile: "./models/.sapConfig.yml" }
  }

  const generateYAML = async () => {
    // Convert PSF to kip/in² (1 PSF = 1/144000 kip/in²)
    const psfToKipPerSqIn = (psf) => psf / 144000

    const { modelsDir, configFile } = await getWorkspacePaths()

    const yamlData = {
      general: {
        units: formState.units,
        model_path: modelsDir,
      },
      materials: {
        steel: {
          name: formState.defaultMaterial,
          type: "STEEL",
        },
      },
      restraints: {
        base_restraints: [
          formState.baseRestraints.UX,
          formState.baseRestraints.UY,
          formState.baseRestraints.UZ,
          formState.baseRestraints.RX,
          formState.baseRestraints.RY,
          formState.baseRestraints.RZ,
        ],
        auto_detect_columns: formState.autoDetectColumns,
      },
      loads: {
        patterns: formState.loadPatterns.split(",").map((pattern) => {
          const trimmedPattern = pattern.trim()
          return {
            name: trimmedPattern,
            type: trimmedPattern,
          }
        }),
        area_loads: {
          floor: {
            dead: psfToKipPerSqIn(formState.floorDeadLoad),
            live: psfToKipPerSqIn(formState.floorLiveLoad),
          },
          roof: {
            dead: psfToKipPerSqIn(formState.roofDeadLoad),
            live: psfToKipPerSqIn(formState.roofLiveLoad),
          },
        },
        load_direction_type: formState.loadDirectionType,
        exclusion_areas: formState.exclusionAreas.map((area) => ({
          x:
            area.x === null
              ? null
              : typeof area.x === "number"
              ? area.x
              : parseFloat(area.x),
          y:
            area.y === null
              ? null
              : typeof area.y === "number"
              ? area.y
              : parseFloat(area.y),
          z:
            area.z === null
              ? null
              : typeof area.z === "number"
              ? area.z
              : parseFloat(area.z),
        })),
      },
      section_candidates: {
        section_types: formState.sectionTypes,
        filter: {
          depth_range: [formState.depthRangeMin, formState.depthRangeMax],
          weight_range: [formState.weightRangeMin, formState.weightRangeMax],
        },
      },
      design: {
        code: formState.designCode,
        maximum_allowed_usage_ratio: formState.maxUsageRatio,
        objective_weights: {
          weight_minimization: formState.weightMinimization,
          connection_compatibility: formState.connectionCompatibility,
          floor_consistency: formState.floorConsistency,
        },
        max_groups: formState.maxGroups,
        beam_column_segregation: formState.beamColumnSegregation,
        group_by_floor: formState.groupByFloor,
      },
    }

    // Convert to YAML string with comment
    const header =
      "# SAP2000 Automation Configuration\n# This file controls the behavior of the structural analysis and optimization\n\n"
    const yamlString = header + jsyaml.dump(yamlData, { lineWidth: -1 })

    // Save the config file into the workspace directory using Electron API
    if (window.electron && window.electron.ipcRenderer) {
      try {
        const result = await window.electron.ipcRenderer.invoke("save-file", {
          filePath: configFile,
          content: yamlString,
        })

        if (result.success) {
          console.log(`SAP configuration saved to ${configFile}`)
          return configFile
        } else {
          console.error("Error saving SAP configuration:", result.error)
          return null
        }
      } catch (error) {
        console.error("Error saving SAP configuration:", error)
        return null
      }
    } else {
      console.error("Electron API not available")
      return null
    }
  }

  const handleSubmit = async (e) => {
    e && e.preventDefault()
    if (isFormComplete) {
      const savedConfigPath = await generateYAML()
      if (savedConfigPath) {
        // Send the saved config file to the backend
        try {
          console.log("Sending config file to backend:", savedConfigPath)
          WebSocketService.loadSAPConfig(savedConfigPath)
        } catch (error) {
          console.error("Error sending config to backend:", error)
        }

        onSubmit()
      }
    }
  }

  if (!isOpen) return null

  // Render different form content based on current step
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="step-content">
            <div className="section">
              <h3>General</h3>
              <div
                className={`form-group ${fieldErrors.units ? "has-error" : ""}`}
              >
                <LabelWithTooltip
                  htmlFor="units"
                  text="Unit system"
                  tooltipKey="units"
                />
                <select
                  id="units"
                  name="units"
                  value={formState.units}
                  onChange={handleInputChange}
                  className="form-control"
                >
                  <option value="">Select unit system</option>
                  <option value="kip-in">kip-in</option>
                  <option value="kip-ft">kip-ft</option>
                  <option value="N-mm">N-mm</option>
                  <option value="N-m">N-m</option>
                </select>
              </div>

              <div
                className={`form-group ${
                  fieldErrors.defaultMaterial ? "has-error" : ""
                }`}
              >
                <LabelWithTooltip
                  htmlFor="defaultMaterial"
                  text="Steel material"
                  tooltipKey="defaultMaterial"
                />
                <input
                  type="text"
                  id="defaultMaterial"
                  name="defaultMaterial"
                  value={formState.defaultMaterial}
                  onChange={handleInputChange}
                  className="form-control"
                  placeholder={
                    fieldErrors.defaultMaterial ? "Required" : "A992Fy50"
                  }
                />
              </div>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="step-content">
            <div className="section">
              <h3>Restraints</h3>
              <div className="form-group checkboxes">
                <label className="checkbox-group-label">
                  Base restraints
                  {tooltipInfo.baseRestraints && (
                    <Tooltip text={tooltipInfo.baseRestraints}>
                      <FontAwesomeIcon
                        icon={faInfoCircle}
                        className="tooltip-icon"
                      />
                    </Tooltip>
                  )}
                </label>
                <div className="checkbox-row">
                  <label>
                    <input
                      type="checkbox"
                      name="baseRestraint_UX"
                      checked={formState.baseRestraints.UX}
                      onChange={handleInputChange}
                    />
                    UX
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      name="baseRestraint_UY"
                      checked={formState.baseRestraints.UY}
                      onChange={handleInputChange}
                    />
                    UY
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      name="baseRestraint_UZ"
                      checked={formState.baseRestraints.UZ}
                      onChange={handleInputChange}
                    />
                    UZ
                  </label>
                </div>
                <div className="checkbox-row">
                  <label>
                    <input
                      type="checkbox"
                      name="baseRestraint_RX"
                      checked={formState.baseRestraints.RX}
                      onChange={handleInputChange}
                    />
                    RX
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      name="baseRestraint_RY"
                      checked={formState.baseRestraints.RY}
                      onChange={handleInputChange}
                    />
                    RY
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      name="baseRestraint_RZ"
                      checked={formState.baseRestraints.RZ}
                      onChange={handleInputChange}
                    />
                    RZ
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="autoDetectColumns"
                    checked={formState.autoDetectColumns}
                    onChange={handleInputChange}
                  />
                  Auto detect columns
                  {tooltipInfo.autoDetectColumns && (
                    <Tooltip text={tooltipInfo.autoDetectColumns}>
                      <FontAwesomeIcon
                        icon={faInfoCircle}
                        className="tooltip-icon"
                      />
                    </Tooltip>
                  )}
                </label>
              </div>
            </div>

            <div className="section-separator"></div>

            <div className="section">
              <h3>Loads</h3>
              <div
                className={`form-group ${
                  fieldErrors.loadPatterns ? "has-error" : ""
                }`}
              >
                <LabelWithTooltip
                  htmlFor="loadPatterns"
                  text="Load patterns (comma separated)"
                  tooltipKey="loadPatterns"
                />
                <select
                  id="loadPatterns"
                  name="loadPatterns"
                  value={formState.loadPatterns}
                  onChange={handleInputChange}
                  className="form-control"
                >
                  <option value="">Select load patterns</option>
                  <option value="DEAD">DEAD</option>
                  <option value="LIVE">LIVE</option>
                  <option value="DEAD, LIVE">DEAD, LIVE</option>
                </select>
              </div>

              <div className="form-row">
                <div
                  className={`form-group half ${
                    fieldErrors.floorDeadLoad ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="floorDeadLoad"
                    text="Floor dead load"
                    tooltipKey="floorDeadLoad"
                  />
                  <input
                    type="number"
                    id="floorDeadLoad"
                    name="floorDeadLoad"
                    value={formState.floorDeadLoad}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={
                      fieldErrors.floorDeadLoad ? "Required" : "50.0"
                    }
                    step="0.1"
                    min="0"
                  />
                </div>

                <div
                  className={`form-group half ${
                    fieldErrors.floorLiveLoad ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="floorLiveLoad"
                    text="Floor live load"
                    tooltipKey="floorLiveLoad"
                  />
                  <input
                    type="number"
                    id="floorLiveLoad"
                    name="floorLiveLoad"
                    value={formState.floorLiveLoad}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={
                      fieldErrors.floorLiveLoad ? "Required" : "50.0"
                    }
                    step="0.1"
                    min="0"
                  />
                </div>
              </div>

              <div className="form-row">
                <div
                  className={`form-group half ${
                    fieldErrors.roofDeadLoad ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="roofDeadLoad"
                    text="Roof dead load"
                    tooltipKey="roofDeadLoad"
                  />
                  <input
                    type="number"
                    id="roofDeadLoad"
                    name="roofDeadLoad"
                    value={formState.roofDeadLoad}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={fieldErrors.roofDeadLoad ? "Required" : "20.0"}
                    step="0.1"
                    min="0"
                  />
                </div>

                <div
                  className={`form-group half ${
                    fieldErrors.roofLiveLoad ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="roofLiveLoad"
                    text="Roof live load"
                    tooltipKey="roofLiveLoad"
                  />
                  <input
                    type="number"
                    id="roofLiveLoad"
                    name="roofLiveLoad"
                    value={formState.roofLiveLoad}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={fieldErrors.roofLiveLoad ? "Required" : "20.0"}
                    step="0.1"
                    min="0"
                  />
                </div>
              </div>

              <div className="form-group">
                <LabelWithTooltip
                  htmlFor="loadDirectionType"
                  text="Load direction type"
                  tooltipKey="loadDirectionType"
                />
                <select
                  id="loadDirectionType"
                  name="loadDirectionType"
                  value={formState.loadDirectionType}
                  onChange={handleInputChange}
                  className="form-control"
                >
                  <option value="DECK_ORIENTED">DECK_ORIENTED</option>
                  <option value="GLOBAL_X">GLOBAL_X</option>
                  <option value="GLOBAL_Y">GLOBAL_Y</option>
                  <option value="GLOBAL_Z">GLOBAL_Z</option>
                </select>
              </div>

              <div className="form-group">
                <label className="checkbox-group-label">
                  Exclusion areas
                  {tooltipInfo.exclusionAreas && (
                    <Tooltip text={tooltipInfo.exclusionAreas}>
                      <FontAwesomeIcon
                        icon={faInfoCircle}
                        className="tooltip-icon"
                      />
                    </Tooltip>
                  )}
                </label>
                <div className="exclusion-areas-container">
                  {formState.exclusionAreas.map((area, index) => (
                    <div key={index} className="exclusion-area-row">
                      <div className="exclusion-area-inputs">
                        <input
                          type="text"
                          placeholder="X (or null)"
                          value={area.x === null ? "null" : area.x}
                          onChange={(e) =>
                            handleExclusionAreaChange(
                              index,
                              "x",
                              e.target.value
                            )
                          }
                          className="form-control exclusion-input"
                        />
                        <input
                          type="text"
                          placeholder="Y (or null)"
                          value={area.y === null ? "null" : area.y}
                          onChange={(e) =>
                            handleExclusionAreaChange(
                              index,
                              "y",
                              e.target.value
                            )
                          }
                          className="form-control exclusion-input"
                        />
                        <input
                          type="text"
                          placeholder="Z (or null)"
                          value={area.z === null ? "null" : area.z}
                          onChange={(e) =>
                            handleExclusionAreaChange(
                              index,
                              "z",
                              e.target.value
                            )
                          }
                          className="form-control exclusion-input"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => removeExclusionArea(index)}
                        className="remove-area-btn"
                        title="Remove exclusion area"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addExclusionArea}
                    className="add-area-btn"
                  >
                    + Add exclusion area
                  </button>
                </div>
              </div>
            </div>
          </div>
        )

      case 3:
        return (
          <div className="step-content">
            <div className="section">
              <h3>Cross-section</h3>
              <div
                className={`form-group ${
                  fieldErrors.sectionTypes ? "has-error" : ""
                }`}
              >
                <LabelWithTooltip
                  htmlFor="sectionTypes"
                  text="Section types"
                  tooltipKey="sectionTypes"
                />
                <div className="section-types">
                  {["W", "HSS", "PIPE", "L", "WT", "C", "MC"].map((type) => (
                    <label key={type} className="section-type-label">
                      <input
                        type="checkbox"
                        checked={formState.sectionTypes.includes(type)}
                        onChange={() => handleSectionTypeChange(type)}
                      />
                      {type}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-row">
                <div
                  className={`form-group half ${
                    fieldErrors.depthRangeMin ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="depthRangeMin"
                    text="Depth range (min)"
                    tooltipKey="depthRange"
                  />
                  <input
                    type="number"
                    id="depthRangeMin"
                    name="depthRangeMin"
                    value={formState.depthRangeMin}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={fieldErrors.depthRangeMin ? "Required" : "6"}
                    min="0"
                  />
                </div>

                <div
                  className={`form-group half ${
                    fieldErrors.depthRangeMax ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="depthRangeMax"
                    text="Depth range (max)"
                    tooltipKey="depthRange"
                  />
                  <input
                    type="number"
                    id="depthRangeMax"
                    name="depthRangeMax"
                    value={formState.depthRangeMax}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={fieldErrors.depthRangeMax ? "Required" : "26"}
                    min="0"
                  />
                </div>
              </div>

              <div className="form-row">
                <div
                  className={`form-group half ${
                    fieldErrors.weightRangeMin ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="weightRangeMin"
                    text="Weight range (min lbs/ft)"
                    tooltipKey="weightRange"
                  />
                  <input
                    type="number"
                    id="weightRangeMin"
                    name="weightRangeMin"
                    value={formState.weightRangeMin}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={fieldErrors.weightRangeMin ? "Required" : "10"}
                    min="0"
                  />
                </div>

                <div
                  className={`form-group half ${
                    fieldErrors.weightRangeMax ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="weightRangeMax"
                    text="Weight range (max lbs/ft)"
                    tooltipKey="weightRange"
                  />
                  <input
                    type="number"
                    id="weightRangeMax"
                    name="weightRangeMax"
                    value={formState.weightRangeMax}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={
                      fieldErrors.weightRangeMax ? "Required" : "360"
                    }
                    min="0"
                  />
                </div>
              </div>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="step-content">
            <div className="section">
              <h3>Optimization</h3>
              <div
                className={`form-group ${
                  fieldErrors.designCode ? "has-error" : ""
                }`}
              >
                <LabelWithTooltip
                  htmlFor="designCode"
                  text="Design code"
                  tooltipKey="designCode"
                />
                <input
                  type="text"
                  id="designCode"
                  name="designCode"
                  value={formState.designCode}
                  onChange={handleInputChange}
                  className="form-control"
                  placeholder={
                    fieldErrors.designCode ? "Required" : "AISC 360-16"
                  }
                />
              </div>

              <div
                className={`form-group ${
                  fieldErrors.maxUsageRatio ? "has-error" : ""
                }`}
              >
                <LabelWithTooltip
                  htmlFor="maxUsageRatio"
                  text="Max usage ratio (0.0-1.0)"
                  tooltipKey="maxUsageRatio"
                />
                <input
                  type="number"
                  id="maxUsageRatio"
                  name="maxUsageRatio"
                  value={formState.maxUsageRatio}
                  onChange={handleInputChange}
                  className="form-control"
                  placeholder={fieldErrors.maxUsageRatio ? "Required" : "0.9"}
                  step="0.01"
                  min="0"
                  max="1"
                />
              </div>

              <div className="form-row">
                <div
                  className={`form-group half ${
                    fieldErrors.weightMinimization ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="weightMinimization"
                    text="Weight minimization"
                    tooltipKey="weightMinimization"
                  />
                  <input
                    type="number"
                    id="weightMinimization"
                    name="weightMinimization"
                    value={formState.weightMinimization}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={
                      fieldErrors.weightMinimization ? "Required" : "1.0"
                    }
                    step="0.1"
                    min="0"
                    max="1"
                  />
                </div>

                <div
                  className={`form-group half ${
                    fieldErrors.connectionCompatibility ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="connectionCompatibility"
                    text="Connection compatibility"
                    tooltipKey="connectionCompatibility"
                  />
                  <input
                    type="number"
                    id="connectionCompatibility"
                    name="connectionCompatibility"
                    value={formState.connectionCompatibility}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={
                      fieldErrors.connectionCompatibility ? "Required" : "0.5"
                    }
                    step="0.1"
                    min="0"
                    max="1"
                  />
                </div>
              </div>

              <div className="form-row">
                <div
                  className={`form-group half ${
                    fieldErrors.floorConsistency ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="floorConsistency"
                    text="Floor consistency"
                    tooltipKey="floorConsistency"
                  />
                  <input
                    type="number"
                    id="floorConsistency"
                    name="floorConsistency"
                    value={formState.floorConsistency}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={
                      fieldErrors.floorConsistency ? "Required" : "0.3"
                    }
                    step="0.1"
                    min="0"
                    max="1"
                  />
                </div>

                <div
                  className={`form-group half ${
                    fieldErrors.maxGroups ? "has-error" : ""
                  }`}
                >
                  <LabelWithTooltip
                    htmlFor="maxGroups"
                    text="Max groups"
                    tooltipKey="maxGroups"
                  />
                  <input
                    type="number"
                    id="maxGroups"
                    name="maxGroups"
                    value={formState.maxGroups}
                    onChange={handleInputChange}
                    className="form-control"
                    placeholder={fieldErrors.maxGroups ? "Required" : "8"}
                    min="1"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group half">
                  <label>
                    <input
                      type="checkbox"
                      name="beamColumnSegregation"
                      checked={formState.beamColumnSegregation}
                      onChange={handleInputChange}
                    />
                    Beam column segregation
                    {tooltipInfo.beamColumnSegregation && (
                      <Tooltip text={tooltipInfo.beamColumnSegregation}>
                        <FontAwesomeIcon
                          icon={faInfoCircle}
                          className="tooltip-icon"
                        />
                      </Tooltip>
                    )}
                  </label>
                </div>

                <div className="form-group half">
                  <label>
                    <input
                      type="checkbox"
                      name="groupByFloor"
                      checked={formState.groupByFloor}
                      onChange={handleInputChange}
                    />
                    Group by floor
                    {tooltipInfo.groupByFloor && (
                      <Tooltip text={tooltipInfo.groupByFloor}>
                        <FontAwesomeIcon
                          icon={faInfoCircle}
                          className="tooltip-icon"
                        />
                      </Tooltip>
                    )}
                  </label>
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="init-sap-config-overlay">
      <div className="init-sap-config-modal">
        <div className="modal-header">
          <div></div>
          <h2>SAP Configuration</h2>
          <div className="close-button">
            <button onClick={onClose} className="close-btn">
              <FontAwesomeIcon icon={faTimes} />
            </button>
          </div>
        </div>

        <div className="step-indicator-container">
          <div className="step-indicator">
            {[
              { number: 1, label: "General" },
              { number: 2, label: "Restraints & Loads" },
              { number: 3, label: "Cross-section" },
              { number: 4, label: "Optimization" },
            ].map((step, index) => (
              <React.Fragment key={step.number}>
                <div
                  className={`step ${
                    step.number === currentStep ? "active" : ""
                  }`}
                  onClick={() => goToStep(step.number)}
                >
                  <div className="step-circle">
                    {stepStatus[step.number] === "complete" ? (
                      <FontAwesomeIcon
                        icon={faCheckCircle}
                        className="step-icon complete"
                      />
                    ) : stepStatus[step.number] === "error" ? (
                      <FontAwesomeIcon
                        icon={faExclamationCircle}
                        className="step-icon error"
                      />
                    ) : (
                      <FontAwesomeIcon
                        icon={faCircle}
                        className="step-icon incomplete"
                      />
                    )}
                  </div>
                  <div className="step-label">{step.label}</div>
                </div>
                {index < 3 && <div className="step-line"></div>}
              </React.Fragment>
            ))}
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (isFormComplete && currentStep === 4) handleSubmit(e)
          }}
        >
          {renderStepContent()}

          <div className="modal-footer">
            <div className="navigation-buttons">
              <button
                type="button"
                className="nav-btn back"
                onClick={prevStep}
                disabled={currentStep === 1}
              >
                Back
              </button>

              {currentStep === 4 ? (
                <button
                  type="button"
                  className={`nav-btn submit ${
                    isFormComplete ? "enabled" : "disabled"
                  }`}
                  disabled={!isFormComplete}
                  onClick={handleSubmit}
                >
                  Submit
                </button>
              ) : (
                <button
                  type="button"
                  className="nav-btn next"
                  onClick={nextStep}
                >
                  Next
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default InitSapConfig
