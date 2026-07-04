const { app } = require("electron")
const fs = require("fs")
const path = require("path")

// Shared with the Python backend: Electron's userData dir for productName
// "Compass" is %APPDATA%/Compass, which is exactly where the backend reads
// settings.json from (see backend/src/compass/runtime_paths.py).
const SETTINGS_FILE = path.join(app.getPath("userData"), "settings.json")

const DEFAULT_SETTINGS = {
  anthropicApiKey: "",
  openaiApiKey: "",
  googleApiKey: "",
  onboardingCompleted: false,
}

function getSettings() {
  try {
    const raw = fs.readFileSync(SETTINGS_FILE, "utf8")
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch (error) {
    return { ...DEFAULT_SETTINGS }
  }
}

function saveSettings(patch) {
  const merged = { ...getSettings(), ...(patch || {}) }
  const dir = path.dirname(SETTINGS_FILE)
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true })
  }
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(merged, null, 2), "utf8")
  return merged
}

/**
 * Settings safe to hand to the renderer. Keys are masked; the renderer only
 * needs to know whether they are set, never their value.
 */
function getSettingsForRenderer() {
  const settings = getSettings()
  return {
    anthropicKeySet: Boolean(settings.anthropicApiKey),
    openaiKeySet: Boolean(settings.openaiApiKey),
    googleKeySet: Boolean(settings.googleApiKey),
    onboardingCompleted: Boolean(settings.onboardingCompleted),
  }
}

module.exports = { getSettings, saveSettings, getSettingsForRenderer, SETTINGS_FILE }
