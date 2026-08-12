"""Socket.IO client + Qt signal bridge (see module docstrings for the Phase
1 finding that limits this to session presence, not realtime data, today).
"""

from app.socket.bridge import SocketBridge
from app.socket.client import SocketClient

__all__ = ["SocketBridge", "SocketClient"]
