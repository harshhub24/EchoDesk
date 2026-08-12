"""OS-specific implementations. Keep everything OS-specific inside
agent/platform/linux.py and agent/platform/windows.py only - every other
module should call agent.platform.common, which picks the right backend.
"""
