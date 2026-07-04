"""Central place for filesystem paths that differ between development and the
frozen (PyInstaller) build.

In development everything lives inside the repo like before. In the frozen
build the executable directory is read-only (Program Files), so all writable
state goes to %APPDATA%/Compass and read-only seed data is looked up inside
the PyInstaller bundle.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

IS_FROZEN = bool(getattr(sys, 'frozen', False))


def get_bundle_dir() -> Path:
    """Directory holding bundled read-only data files.

    PyInstaller extracts/installs data files under sys._MEIPASS (onefile) or
    <app>/_internal (onedir, where _MEIPASS also points). In development this
    is the backend/src directory.
    """
    if IS_FROZEN:
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def get_appdata_dir() -> Path:
    """Writable per-user application data directory (%APPDATA%/Compass)."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    path = Path(appdata) / 'Compass'
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    if IS_FROZEN:
        path = get_appdata_dir() / 'logs'
    else:
        # Preserve the historical dev behaviour (backend/logs relative to cwd)
        path = Path('logs')
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_workspace_dir() -> Path:
    """Directory for user-facing artifacts (SAP models, generated configs).

    Priority: WORKSPACE_FOLDER env var (set by Electron in production, or by
    the developer) -> Documents/Compass when frozen -> repo root in dev.
    """
    env_dir = os.environ.get('WORKSPACE_FOLDER')
    if env_dir:
        path = Path(env_dir)
    elif IS_FROZEN:
        path = Path(os.path.expanduser('~')) / 'Documents' / 'Compass'
    else:
        cwd = Path(os.getcwd())
        path = cwd.parent if cwd.name == 'backend' else cwd
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_settings() -> dict:
    """Read the shared settings file written by the Electron shell.

    Electron's userData dir for productName "Compass" is %APPDATA%/Compass,
    so both processes agree on this location without extra plumbing.
    """
    settings_path = get_appdata_dir() / 'settings.json'
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning(f"Could not read settings file {settings_path}: {e}")
        return {}


def get_rag_db_dir() -> Path:
    """Location of the SAP2000 API ChromaDB. Seeded from the bundle when frozen."""
    override = os.environ.get('COMPASS_RAG_DB_DIR')
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path
    if not IS_FROZEN:
        return Path(__file__).resolve().parent / 'database' / 'sap2000_api'
    return get_appdata_dir() / 'database' / 'sap2000_api'


def get_template_db_path() -> Path:
    """Location of the (writable) template-training sqlite database."""
    override = os.environ.get('COMPASS_TEMPLATE_DB_PATH')
    if override:
        path = Path(override)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    if not IS_FROZEN:
        return Path(__file__).resolve().parent / 'database' / 'template_database.db'
    path = get_appdata_dir() / 'database' / 'template_database.db'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def seed_user_data() -> None:
    """Copy bundled seed databases into %APPDATA%/Compass.

    The RAG documentation database is a read-only artifact shipped with the
    app, so the AppData copy is treated as a cache: it is (re)seeded whenever
    the bundled version differs from what was seeded before (tracked via a
    fingerprint marker). This also recovers from stale/empty databases left
    behind by older versions. No-op in development.
    """
    if not IS_FROZEN:
        return

    bundled_db = get_bundle_dir() / 'compass' / 'database' / 'sap2000_api'
    target_db = get_rag_db_dir()
    marker = target_db / '.seed_fingerprint'
    try:
        bundled_sqlite = bundled_db / 'chroma.sqlite3'
        if bundled_db.is_dir() and bundled_sqlite.is_file():
            fingerprint = str(bundled_sqlite.stat().st_size)
            current = marker.read_text().strip() if marker.exists() else None
            if current != fingerprint:
                logger.info(f"Seeding RAG database from {bundled_db} to {target_db}")
                if target_db.exists():
                    shutil.rmtree(target_db)
                shutil.copytree(bundled_db, target_db)
                marker.write_text(fingerprint)
    except Exception as e:
        logger.error(f"Failed to seed RAG database: {e}")

    bundled_template_db = get_bundle_dir() / 'compass' / 'database' / 'template_database.db'
    target_template_db = get_template_db_path()
    try:
        if bundled_template_db.is_file() and not target_template_db.exists():
            target_template_db.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(bundled_template_db, target_template_db)
    except Exception as e:
        logger.error(f"Failed to seed template database: {e}")


def setup_comtypes_cache() -> None:
    """Make comtypes write its generated COM wrappers to a writable directory.

    Inside a frozen app the comtypes.gen package lives in the read-only
    bundle. comtypes has its own frozen-app fallback, but it depends on the
    bundled comtypes.gen being importable and writable checks behaving; being
    explicit removes that failure mode entirely.
    """
    if not IS_FROZEN:
        return
    try:
        import comtypes.client
        gen_dir = get_appdata_dir() / 'comtypes_gen'
        gen_dir.mkdir(parents=True, exist_ok=True)
        init_py = gen_dir / '__init__.py'
        if not init_py.exists():
            init_py.write_text('# comtypes code generation cache\n')
        comtypes.client.gen_dir = str(gen_dir)
        # Make the redirected package importable as comtypes.gen
        import comtypes.gen
        if str(gen_dir) not in comtypes.gen.__path__:
            comtypes.gen.__path__.insert(0, str(gen_dir))
        logger.info(f"comtypes code cache redirected to {gen_dir}")
    except Exception as e:
        logger.error(f"Failed to set up comtypes cache: {e}")
