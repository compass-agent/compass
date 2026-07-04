"""API key resolution.

Keys are resolved on demand, in priority order:
1. Environment variables (set by the Electron shell when it spawns the
   backend, or by the developer).
2. The shared settings file %APPDATA%/Compass/settings.json written by the
   app's onboarding/settings UI.

Prefer the get_*_api_key() functions: they re-read the settings file each
call, so a key saved by the UI takes effect on the next agent initialization
without restarting the backend. The module-level constants exist for
backwards compatibility and are snapshots taken at import time.

Never hardcode keys in this file.
"""

import os

from compass.runtime_paths import get_settings


def _resolve(env_name: str, settings_name: str) -> str:
    value = os.environ.get(env_name) or get_settings().get(settings_name) or ""
    return value.strip()


def get_anthropic_api_key() -> str:
    return _resolve('ANTHROPIC_API_KEY', 'anthropicApiKey')


def get_openai_api_key() -> str:
    return _resolve('OPENAI_API_KEY', 'openaiApiKey')


def get_google_api_key() -> str:
    return _resolve('GOOGLE_API_KEY', 'googleApiKey')


# Backwards-compatible import-time snapshots.
ANTHROPIC_API_KEY = get_anthropic_api_key()
OPENAI_API_KEY = get_openai_api_key()
GOOGLE_API_KEY = get_google_api_key()
