import React from "react"
import { createRoot } from "react-dom/client"
import { AppProvider } from "../common/context/AppContext"
import TemplateTraining from "./TemplateTraining"

console.log("Template Training index.js is executing")

const container = document.getElementById("root")
if (!container) {
  console.error("Root element not found")
} else {
  console.log("Root element found, creating React root")
  const root = createRoot(container)
  root.render(
    <AppProvider>
      <TemplateTraining />
    </AppProvider>
  )
}
