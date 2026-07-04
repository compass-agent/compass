import {
  faCheckCircle,
  faExclamationCircle,
  faSpinner,
  faTimes,
} from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import React, { useEffect, useRef, useState } from "react"
import WebSocketService from "../../common/services/websocket"
import "../styles/SettingsModal.scss"

const VALIDATION_TIMEOUT_MS = 20000

/**
 * First-run onboarding and settings dialog.
 *
 * Collects the LLM API keys the agent needs:
 * - Anthropic API key (required - powers the agent)
 * - OpenAI API key (optional - powers SAP2000 documentation search)
 *
 * Keys are validated against the provider through the backend, then saved
 * to the shared settings file, after which the agent is (re)initialized.
 */
const SettingsModal = ({ isOpen, onClose, isFirstRun, connected }) => {
  const [anthropicKey, setAnthropicKey] = useState("")
  const [openaiKey, setOpenaiKey] = useState("")
  const [savedState, setSavedState] = useState({
    anthropicKeySet: false,
    openaiKeySet: false,
  })
  const [phase, setPhase] = useState("idle") // idle | validating | saving | done
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const pendingValidation = useRef(null)

  // Load which keys are already saved (masked - values never leave main process)
  useEffect(() => {
    if (isOpen && window.electron?.settings?.get) {
      window.electron.settings
        .get()
        .then((s) => setSavedState(s))
        .catch(() => {})
      setError(null)
      setSuccessMessage(null)
      setAnthropicKey("")
      setOpenaiKey("")
      setPhase("idle")
    }
  }, [isOpen])

  // Route validation results to the pending promise
  useEffect(() => {
    const handler = (data) => {
      const pending = pendingValidation.current
      if (pending && data.provider === pending.provider) {
        pendingValidation.current = null
        clearTimeout(pending.timer)
        pending.resolve(data)
      }
    }
    WebSocketService.addHandler("onApiKeyValidation", handler)
    return () => WebSocketService.removeHandler("onApiKeyValidation", handler)
  }, [])

  const validateKey = (provider, apiKey) =>
    new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingValidation.current = null
        reject(new Error("Validation timed out. Is the backend running?"))
      }, VALIDATION_TIMEOUT_MS)
      pendingValidation.current = { provider, resolve, timer }
      WebSocketService.validateApiKey(provider, apiKey)
    })

  const handleSave = async () => {
    setError(null)
    setSuccessMessage(null)

    const newAnthropic = anthropicKey.trim()
    const newOpenai = openaiKey.trim()

    if (!newAnthropic && !savedState.anthropicKeySet) {
      setError("An Anthropic API key is required for the agent to work.")
      return
    }
    if (!newAnthropic && !newOpenai) {
      // Nothing new entered; treat as "keep existing keys"
      completeOnboarding()
      return
    }

    try {
      if (connected) {
        setPhase("validating")
        if (newAnthropic) {
          const result = await validateKey("anthropic", newAnthropic)
          if (!result.valid) {
            throw new Error(`Anthropic key: ${result.error || "invalid"}`)
          }
        }
        if (newOpenai) {
          const result = await validateKey("openai", newOpenai)
          if (!result.valid) {
            throw new Error(`OpenAI key: ${result.error || "invalid"}`)
          }
        }
      }

      setPhase("saving")
      const patch = { onboardingCompleted: true }
      if (newAnthropic) patch.anthropicApiKey = newAnthropic
      if (newOpenai) patch.openaiApiKey = newOpenai
      const saveResult = await window.electron.settings.save(patch)
      if (!saveResult?.success) {
        throw new Error(saveResult?.error || "Could not save settings")
      }

      // Ask the backend to pick up the new keys immediately
      WebSocketService.initializeAgent()

      setPhase("done")
      setSuccessMessage("Saved. The agent is ready to use.")
      setTimeout(() => onClose(), 1200)
    } catch (e) {
      setPhase("idle")
      setError(e.message)
    }
  }

  const completeOnboarding = async () => {
    try {
      await window.electron.settings.save({ onboardingCompleted: true })
    } catch (_) {
      /* non-fatal */
    }
    onClose()
  }

  if (!isOpen) return null

  const busy = phase === "validating" || phase === "saving"

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal">
        <div className="settings-modal-header">
          <h2>{isFirstRun ? "Welcome to Compass" : "Settings"}</h2>
          {!isFirstRun && (
            <button className="settings-close-btn" onClick={onClose}>
              <FontAwesomeIcon icon={faTimes} />
            </button>
          )}
        </div>

        <div className="settings-modal-body">
          {isFirstRun && (
            <p className="settings-intro">
              Compass is an AI copilot for SAP2000. To get started, add your
              Anthropic API key - this powers the AI agent. You can get a key
              at <span className="mono">console.anthropic.com</span>.
            </p>
          )}

          {!connected && (
            <div className="settings-warning">
              <FontAwesomeIcon icon={faExclamationCircle} /> Backend is not
              connected yet - keys will be saved without validation.
            </div>
          )}

          <div className="settings-field">
            <label>
              Anthropic API key <span className="required">(required)</span>
              {savedState.anthropicKeySet && (
                <span className="key-saved">
                  <FontAwesomeIcon icon={faCheckCircle} /> saved
                </span>
              )}
            </label>
            <input
              type="password"
              placeholder={
                savedState.anthropicKeySet
                  ? "•••••••• (enter a new key to replace)"
                  : "sk-ant-..."
              }
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              disabled={busy}
              autoFocus={isFirstRun}
            />
            <div className="field-hint">Powers the structural engineering agent.</div>
          </div>

          <div className="settings-field">
            <label>
              OpenAI API key <span className="optional">(optional)</span>
              {savedState.openaiKeySet && (
                <span className="key-saved">
                  <FontAwesomeIcon icon={faCheckCircle} /> saved
                </span>
              )}
            </label>
            <input
              type="password"
              placeholder={
                savedState.openaiKeySet
                  ? "•••••••• (enter a new key to replace)"
                  : "sk-..."
              }
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              disabled={busy}
            />
            <div className="field-hint">
              Enables semantic search of the SAP2000 API documentation
              (recommended for best results).
            </div>
          </div>

          {error && (
            <div className="settings-error">
              <FontAwesomeIcon icon={faExclamationCircle} /> {error}
            </div>
          )}
          {successMessage && (
            <div className="settings-success">
              <FontAwesomeIcon icon={faCheckCircle} /> {successMessage}
            </div>
          )}
        </div>

        <div className="settings-modal-footer">
          {isFirstRun && (
            <button
              className="settings-btn secondary"
              onClick={completeOnboarding}
              disabled={busy}
            >
              Skip for now
            </button>
          )}
          <button
            className="settings-btn primary"
            onClick={handleSave}
            disabled={busy}
          >
            {busy ? (
              <>
                <FontAwesomeIcon icon={faSpinner} spin />{" "}
                {phase === "validating" ? "Validating..." : "Saving..."}
              </>
            ) : isFirstRun ? (
              "Save & Continue"
            ) : (
              "Save"
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsModal
