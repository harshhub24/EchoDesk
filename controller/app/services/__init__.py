"""Business logic layer. Views never import app/api or app/socket
directly - everything routes through AppState (or a service that itself
only touches AppState.rest_client).
"""

from app.services.app_state import AppState

__all__ = ["AppState"]
