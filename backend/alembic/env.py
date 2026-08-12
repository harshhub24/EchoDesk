"""Alembic environment for manual migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context

from app.create_app import create_app
from app.extensions import db


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = db.metadata


def get_app():
    return create_app(os.getenv("FLASK_ENV", "development"))


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = get_app().config["SQLALCHEMY_DATABASE_URI"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    app = get_app()
    with app.app_context():
        connection = db.engine.connect()
        try:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
        finally:
            connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
