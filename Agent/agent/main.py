"""EchoDesk Agent entry point.

Do not run this file directly (`python agent/main.py`) - use the repo-root
`run.py` instead, or `python -m agent.main` from the directory that
*contains* `agent/`. See run.py's docstring for why (stdlib socket/platform
shadowing).
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
import time

from agent.api import endpoints
from agent.api.auth import EnrollmentError, ensure_authenticated
from agent.api.client import ApiError, RestClient
from agent.commands.dispatcher import CommandDispatcher
from agent.config import load_config
from agent.socket.client import SocketClient
from agent.socket.events import register_command_handler
from agent.system import device as device_info
from agent.utils.logger import setup_logging
from agent.heartbeat.heartbeat import HeartbeatLoop

logger = logging.getLogger("agent.main")

_COMMAND_POLL_INTERVAL_SECONDS = 15
_FLUSH_INTERVAL_SECONDS = 5
_SOCKET_RETRY_DELAY_SECONDS = 10


class Agent:
    def __init__(self) -> None:
        self.config = load_config()
        self.config.ensure_directories()
        setup_logging(self.config.log_dir, self.config.log_level)

        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

        self.local_device_id = device_info.load_or_create_device_id(self.config.data_dir)
        self.rest_client = RestClient(self.config)
        self.socket_client: SocketClient | None = None
        self.dispatcher: CommandDispatcher | None = None
        self.heartbeat_loop: HeartbeatLoop | None = None

    # --- Startup -----------------------------------------------------------------------

    def _enroll(self) -> str:
        try:
            return ensure_authenticated(self.rest_client, self.config, self.config.data_dir, self.local_device_id)
        except EnrollmentError as error:
            logger.critical("Cannot start: %s", error)
            sys.exit(1)
        except ApiError as error:
            logger.critical("Enrollment failed talking to backend: %s", error)
            sys.exit(1)

    def start(self) -> None:
        logger.info("Starting EchoDesk Agent (device_id=%s)", self.local_device_id)
        static_info = device_info.collect_static_system_info()
        logger.info("System: %s", static_info)

        api_key = self._enroll()

        self.socket_client = SocketClient(self.config, api_key)
        self.dispatcher = CommandDispatcher(
            rest_client=self.rest_client,
            socket_client=self.socket_client,
            file_root=self.config.file_manager_root,
        )
        register_command_handler(self.socket_client, self.dispatcher.handle)

        self.heartbeat_loop = HeartbeatLoop(
            self.rest_client, self.config.heartbeat_interval_seconds, self.socket_client
        )
        self.heartbeat_loop.start()

        self._spawn_thread(self._run_socket_connection_loop, "socket-connect")
        self._spawn_thread(self._run_command_poll_loop, "command-poll")
        self._spawn_thread(self._run_flush_loop, "flush-pending")

        logger.info("Agent started successfully")

    def _spawn_thread(self, target, name: str) -> None:
        thread = threading.Thread(target=target, name=name, daemon=True)
        thread.start()
        self._threads.append(thread)

    # --- Background loops ----------------------------------------------------------------

    def _run_socket_connection_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if not self.socket_client.connected:
                    self.socket_client.connect()
                    if self.dispatcher:
                        self.dispatcher.flush_pending()
            except Exception as error:
                logger.warning("Socket connect attempt failed, will retry: %s", error)
            self._stop_event.wait(_SOCKET_RETRY_DELAY_SECONDS)

    def _run_command_poll_loop(self) -> None:
        # REST fallback: catches anything missed while the socket was down,
        # and covers the window before the very first socket connection.
        while not self._stop_event.is_set():
            try:
                commands = endpoints.fetch_pending_commands(self.rest_client)
                for command in commands:
                    self.dispatcher.handle(command)
            except ApiError as error:
                logger.warning("Polling pending commands failed: %s", error)
            self._stop_event.wait(_COMMAND_POLL_INTERVAL_SECONDS)

    def _run_flush_loop(self) -> None:
        while not self._stop_event.is_set():
            if self.dispatcher:
                self.dispatcher.flush_pending()
            self._stop_event.wait(_FLUSH_INTERVAL_SECONDS)

    # --- Shutdown ----------------------------------------------------------------------

    def stop(self) -> None:
        logger.info("Shutting down Agent...")
        self._stop_event.set()

        if self.heartbeat_loop:
            self.heartbeat_loop.stop()
        if self.socket_client:
            self.socket_client.disconnect()
        for thread in self._threads:
            thread.join(timeout=5)
        self.rest_client.close()
        logger.info("Agent stopped cleanly")

    def run_forever(self) -> None:
        self.start()

        def _handle_signal(signum, _frame):
            logger.info("Received signal %s", signum)
            self._stop_event.set()

        try:
            signal.signal(signal.SIGINT, _handle_signal)
            signal.signal(signal.SIGTERM, _handle_signal)
        except (ValueError, AttributeError):
            # signal() only works on the main thread / not all platforms
            # support SIGTERM the same way (e.g. some Windows contexts) -
            # non-fatal, the service manager's own stop mechanism still works.
            logger.debug("Could not install signal handlers in this context")

        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def main() -> None:
    agent = Agent()
    agent.run_forever()


if __name__ == "__main__":
    main()
