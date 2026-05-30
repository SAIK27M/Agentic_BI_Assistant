from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent
DATABASE_PATH = APP_ROOT / "data.db"


def _load_single_env_file(env_path):
    if not env_path.exists():
        return

    import os

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not os.environ.get(key):
            os.environ[key] = value


def load_env_file(path=None):
    if path:
        _load_single_env_file(Path(path))
        return

    for env_path in (PROJECT_ROOT / ".env", APP_ROOT / ".env"):
        _load_single_env_file(env_path)
