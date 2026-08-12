"""Small retry/backoff helpers shared by the REST client and socket client.

Wraps tenacity so the rest of the codebase doesn't need to think about retry
policy details in more than one place.
"""

from __future__ import annotations

import logging

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger("agent.utils.retry")


def network_retry(max_attempts: int = 5, *exception_types: type[BaseException]):
    """Decorator: retry on network-ish exceptions with exponential backoff + jitter."""

    exception_types = exception_types or (Exception,)

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception_type(exception_types),
        before_sleep=lambda retry_state: logger.warning(
            "Retrying after error (attempt %s/%s): %s",
            retry_state.attempt_number,
            max_attempts,
            retry_state.outcome.exception() if retry_state.outcome else "unknown",
        ),
    )
