import React, { useState } from "react"
import { VIEW_STATES } from "../constants/viewStates"

const MenuItem = ({ label, selected, onClick }) => (
  <div
    className={`settings-menu-item${selected ? " selected" : ""}`}
    onClick={onClick}
    style={{
      padding: "8px 12px",
      cursor: "pointer",
      color: selected ? "#E0E0E0" : "#9C9B9F",
      background: selected ? "rgba(255,255,255,0.06)" : "transparent",
      borderRadius: "6px",
    }}
  >
    {label}
  </div>
)

const Settings = ({ onNavigate }) => {
  const [section, setSection] = useState("General")

  const openSection = (name) => {
    setSection(name)
    if (name === "Agent Hub") {
      onNavigate(VIEW_STATES.AGENT_HUB)
    }
    // Docs stays within Settings like Models/General
  }

  return (
    <div style={{ display: "flex", height: "100%", color: "#E0E0E0" }}>
      {/* Sidebar */}
      <div
        style={{
          width: "240px",
          padding: "12px",
          borderRight: "1px solid #3D3D3D",
        }}
      >
        {/* User avatar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            marginBottom: "12px",
          }}
        >
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: "#4A4A4A",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 600,
            }}
          >
            M
          </div>
          <div style={{ fontSize: "12px", color: "#CFCFCF" }}>
            Mohammad.k.sadoughi@gmail.com
          </div>
        </div>

        <MenuItem
          label="General"
          selected={section === "General"}
          onClick={() => openSection("General")}
        />
        <MenuItem
          label="Models"
          selected={section === "Models"}
          onClick={() => openSection("Models")}
        />
        <MenuItem
          label="Agent Hub"
          selected={false}
          onClick={() => openSection("Agent Hub")}
        />
        <MenuItem
          label="Docs"
          selected={section === "Docs"}
          onClick={() => openSection("Docs")}
        />
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: "16px" }}>
        <h2 style={{ margin: 0, marginBottom: "8px" }}>Settings</h2>
        <h3 style={{ marginTop: 0 }}>{section}</h3>
        <div style={{ fontSize: "13px", color: "#9C9B9F" }}>
          Placeholder settings for {section}.
        </div>
      </div>
    </div>
  )
}

export default Settings
