import os
import json
import threading
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass()
class GoogleCredential:
    api_key: str
    project_id: str
    name: Optional[str] = field(default=None)

    def __post_init__(self):
        if not self.api_key or not self.project_id:
            raise ValueError("Both 'api_key' and 'project_id' must be provided.")


class GoogleCredentialManager:
    """Thread-safe round-robin manager for Google API credentials."""

    def __init__(self, credentials: List[GoogleCredential]):
        if not credentials:
            raise ValueError("No Google API credentials provided.")
        self._credentials = credentials
        self._index = 0
        self._lock = threading.Lock()

    def get_next(self) -> GoogleCredential:
        """Returns the next credential in round-robin fashion."""
        with self._lock:
            cred = self._credentials[self._index]
            self._index = (self._index + 1) % len(self._credentials)
            return cred

    def __len__(self):
        return len(self._credentials)

    def __repr__(self):
        return f"GoogleCredentialManager({len(self._credentials)} credentials)"


def load_credentials_from_env() -> List[GoogleCredential]:
    """Load credentials from either GOOGLE_API_CREDENTIALS or key/project pair env vars."""
    # First try JSON format
    raw = os.getenv("GOOGLE_API_CREDENTIALS")
    if raw:
        try:
            parsed = json.loads(raw)
            return [
                GoogleCredential(
                    api_key=entry["api_key"],
                    project_id=entry["project_id"],
                    name=entry.get("name")
                )
                for entry in parsed
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError("Invalid JSON format in GOOGLE_API_CREDENTIALS") from e

    # Fallback: comma-separated format
    keys_str = os.getenv("GOOGLE_API_KEYS")
    projects_str = os.getenv("GOOGLE_API_PROJECTS")

    if keys_str and projects_str:
        keys = [k.strip() for k in keys_str.split(",")]
        projects = [p.strip() for p in projects_str.split(",")]

        if len(keys) != len(projects):
            raise ValueError("GOOGLE_API_KEYS and GOOGLE_API_PROJECTS must have the same number of items")

        return [
            GoogleCredential(api_key=key, project_id=proj, name=f"credential_{i+1}")
            for i, (key, proj) in enumerate(zip(keys, projects))
        ]

    raise ValueError("No valid Google API credentials found in environment variables.")


# Global manager instance
_google_credential_manager: Optional[GoogleCredentialManager] = None

def initialize_google_credential_manager():
    global _google_credential_manager
    if _google_credential_manager is None:
        creds = load_credentials_from_env()
        _google_credential_manager = GoogleCredentialManager(creds)
    return _google_credential_manager

def get_next_google_credential() -> GoogleCredential:
    """Returns the next GoogleCredential instance."""
    manager = initialize_google_credential_manager()
    return manager.get_next()
