"""Backend settings, shared by the app and scripts.

Resolution order (highest priority first), so that git worktrees work without copying secrets:
  1. process environment variables
  2. <this worktree>/backend/.env.local   per-worktree overrides (ports, namespace, concurrency)
  3. <this worktree>/backend/.env
  4. <main worktree>/backend/.env         shared secrets, found via the worktree's .git file
See docs/requirements/13-setup.md ("Parallel worktrees").
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent


def main_worktree_dir(repo_dir: Path = REPO_DIR) -> Path:
    """Return the main worktree for a linked worktree, else repo_dir itself."""
    git = repo_dir / ".git"
    if not git.is_file():  # main worktree (a .git directory) or not a git checkout
        return repo_dir
    gitdir = Path(git.read_text(encoding="utf-8").split("gitdir:", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = (repo_dir / gitdir).resolve()
    commondir = gitdir / "commondir"
    common = (
        (gitdir / commondir.read_text(encoding="utf-8").strip()).resolve()
        if commondir.exists()
        else gitdir
    )
    return common.parent


def env_files() -> list[Path]:
    """Existing env files, lowest priority first (later files override earlier ones)."""
    candidates = [
        main_worktree_dir() / "backend" / ".env",
        BACKEND_DIR / ".env",
        BACKEND_DIR / ".env.local",
    ]
    unique = list(dict.fromkeys(p.resolve() for p in candidates))
    return [p for p in unique if p.is_file()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_mode: str = "live"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_port: int = 5173
    # Prefix for Graphiti group_ids, so parallel worktrees sharing one Neo4j never touch each
    # other's data. Defaults to the worktree directory name.
    case_namespace: str = ""

    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    graphiti_telemetry_enabled: bool = False
    semaphore_limit: int = 4

    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-flash"
    llm_small_model: str = "deepseek-flash"
    llm_structured_output: str = "json_object"
    llm_provider_profile: str = "deepseek"

    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    embedding_dim: int = 1024

    @property
    def namespace(self) -> str:
        return _slug(self.case_namespace or REPO_DIR.name)

    def group_id(self, case_id: str) -> str:
        """Graphiti group_id for a case: '<namespace>__<case_id>' (letters, digits, '_' and '-')."""
        return f"{self.namespace}__{_slug(case_id)}"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-") or "default"


@lru_cache
def get_settings() -> Settings:
    settings = Settings(_env_file=env_files())  # type: ignore[call-arg]
    # Graphiti reads these from os.environ at import / construction time.
    os.environ.setdefault(
        "GRAPHITI_TELEMETRY_ENABLED", str(settings.graphiti_telemetry_enabled).lower()
    )
    os.environ.setdefault("SEMAPHORE_LIMIT", str(settings.semaphore_limit))
    return settings
