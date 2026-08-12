"""Display formatting helpers shared across views/widgets."""

from __future__ import annotations

import datetime


def format_bytes(value: float | None) -> str:
    if value is None:
        return "—"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_mb(value: float | None) -> str:
    if value is None:
        return "—"
    return format_bytes(value * 1024 * 1024)


def format_gb(value: float | None) -> str:
    if value is None:
        return "—"
    return format_bytes(value * 1024 * 1024 * 1024)


def format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f}%"


def parse_backend_timestamp(value: str | None) -> datetime.datetime | None:
    """Backend timestamps are ISO 8601, sometimes naive UTC (no offset
    suffix) - same quirk the Agent had to handle. Always returns an
    aware (UTC) datetime, or None.
    """

    if not value:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed


def format_relative_time(value: str | None) -> str:
    """'3 minutes ago' style formatting for last_seen_at / created_at fields."""

    parsed = parse_backend_timestamp(value)
    if parsed is None:
        return "Never"

    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - parsed
    seconds = delta.total_seconds()

    if seconds < 0:
        return "Just now"
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(seconds // 86400)
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    return parsed.strftime("%b %d, %Y")


def format_uptime(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)
