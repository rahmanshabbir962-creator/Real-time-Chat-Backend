"""Alembic environment managed by Flask-Migrate."""
from logging.config import fileConfig

from alembic import context
from flask import current_app

config = context.config

# The restored alembic.ini includes these sections. Guarding this also keeps
# programmatic Alembic invocations working when no config file is supplied.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_db = current_app.extensions["migrate"].db


def get_engine():
    """Return Flask-SQLAlchemy's engine across supported extension versions."""
    try:
        return target_db.engine
    except AttributeError:
        return target_db.get_engine()


def get_engine_url():
    url = get_engine().url.render_as_string(hide_password=False)
    # ConfigParser treats percent signs specially.
    return url.replace("%", "%%")


def get_metadata():
    """Support both single-bind and Flask-SQLAlchemy multi-bind metadata."""
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    context.configure(
        url=get_engine_url(),
        target_metadata=get_metadata(),
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configure_args = current_app.extensions["migrate"].configure_args.copy()
    configure_args.setdefault("compare_type", True)
    configure_args["target_metadata"] = get_metadata()

    with get_engine().connect() as connection:
        context.configure(connection=connection, **configure_args)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
