"""Command lifecycle and queue operations."""

from __future__ import annotations

from datetime import timedelta

from app.constants import COMMAND_TYPES, CommandStatus
from app.extensions import db
from app.models import Command, CommandResult, Device, User
from app.utils.time import utcnow


def validate_command_type(command_type: str) -> str:
    if command_type not in COMMAND_TYPES:
        raise ValueError("Unsupported command type")
    return command_type


def validate_ack_status(execution_status: str) -> str:
    allowed_statuses = {
        CommandStatus.EXECUTING.value,
        CommandStatus.DELIVERED.value,
    }
    normalized_status = execution_status.strip().lower()
    if normalized_status not in allowed_statuses:
        raise ValueError("Unsupported execution status")
    return normalized_status


def validate_result_status(execution_status: str) -> str:
    allowed_statuses = {
        CommandStatus.SUCCESS.value,
        CommandStatus.FAILED.value,
    }
    normalized_status = execution_status.strip().lower()
    if normalized_status not in allowed_statuses:
        raise ValueError("Unsupported result status")
    return normalized_status


def create_command(user: User, device: Device, command_type: str, payload: dict | None = None) -> Command:
    validate_command_type(command_type)
    command = Command(
        device_id=device.id,
        created_by_id=user.id,
        command_type=command_type,
        payload=payload or {},
        status=CommandStatus.PENDING.value,
        expires_at=utcnow() + timedelta(minutes=10),
    )
    db.session.add(command)
    db.session.commit()
    return command


def list_commands(owner_id: str) -> list[Command]:
    return (
        Command.query.join(Device, Command.device_id == Device.id)
        .filter(Device.owner_id == owner_id)
        .order_by(Command.created_at.desc())
        .all()
    )


def list_pending_commands_for_device(device_id: str) -> list[Command]:
    return Command.query.filter_by(device_id=device_id, status=CommandStatus.PENDING.value).order_by(Command.created_at.asc()).all()


def mark_command_delivered(command: Command) -> Command:
    command.status = CommandStatus.DELIVERED.value
    command.delivered_at = utcnow()
    db.session.commit()
    return command


def mark_command_executing(command: Command) -> Command:
    command.status = CommandStatus.EXECUTING.value
    command.started_at = utcnow()
    db.session.commit()
    return command


def record_command_result(command: Command, execution_status: str, output: dict | None = None, raw_payload: dict | None = None) -> CommandResult:
    normalized_status = validate_result_status(execution_status)
    command.status = normalized_status
    command.completed_at = utcnow()
    result = command.result or CommandResult(command_id=command.id, execution_status=normalized_status, output=output or {}, raw_payload=raw_payload or {}, finished_at=utcnow())
    result.execution_status = normalized_status
    result.output = output or {}
    result.raw_payload = raw_payload or {}
    result.finished_at = utcnow()
    db.session.add(result)
    db.session.commit()
    return result


def expire_command(command: Command) -> Command:
    command.status = CommandStatus.EXPIRED.value
    db.session.commit()
    return command

