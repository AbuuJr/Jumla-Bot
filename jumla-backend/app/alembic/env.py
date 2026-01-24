"""
alembic/env.py
Async Alembic environment with robust SSL handling for asyncpg/Neon
and extended debug logging to quickly diagnose connection issues.

Behaviour:
- Reads settings.DATABASE_URL (unchanged)
- Parses out 'ssl' and 'sslmode' query params
- If SSL is requested, creates an ssl.SSLContext and passes it to asyncpg via connect_args
- If SSL params are present but cannot be passed as query params, they are removed
- Prints debug info to stdout so you can inspect what's being used
"""
import asyncio
import ssl
import traceback
from logging.config import fileConfig
from pathlib import Path
import sys
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from alembic import context

# --- Project root & python path ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- Import your models & settings ---
from app.models import Base
from app.config import settings

# --- Alembic Config object ---
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# logging config (alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine with careful SSL handling."""

    async def do_run_migrations():
        original_url = settings.DATABASE_URL
        print("[DEBUG] Original DATABASE_URL:", original_url)

        # Parse URL and its query
        parsed = urlparse(original_url)
        query = dict(parse_qsl(parsed.query))
        print("[DEBUG] Parsed query params:", query)

        # Decide SSL handling based on query params (do NOT mutate settings.DATABASE_URL)
        want_ssl = False
        sslctx = None

        # Check common flags that may indicate SSL
        ssl_param = query.pop("ssl", None)
        sslmode_param = query.pop("sslmode", None)

        if ssl_param is not None:
            val = ssl_param.lower()
            if val in ("1", "true", "yes", "on"):
                want_ssl = True
            elif val in ("0", "false", "no", "off"):
                want_ssl = False
            else:
                # unknown value — print and treat as True for safety
                print(f"[DEBUG] Unknown ssl param value: {ssl_param!r}, treating as True")
                want_ssl = True

        if sslmode_param is not None:
            # sslmode values: disable, allow, prefer, require, verify-ca, verify-full
            print("[DEBUG] Found sslmode param:", sslmode_param)
            sm = sslmode_param.lower()
            if sm == "disable":
                want_ssl = False
            else:
                # for 'require' and verify-* we enable SSL
                want_ssl = True

        # Rebuild patched URL with ssl & sslmode removed (asyncpg mustn't get those query params)
        patched_query = {k: v for k, v in query.items()}
        patched = parsed._replace(query=urlencode(patched_query))
        patched_url = urlunparse(patched)

        # Decide connect_args for asyncpg
        connect_args = {}
        if want_ssl:
            try:
                # Create a default SSL context (system CA certs). This is the correct approach for asyncpg.
                sslctx = ssl.create_default_context()
                # If you need to skip cert verification locally (not recommended), uncomment:
                # sslctx.check_hostname = False
                # sslctx.verify_mode = ssl.CERT_NONE
                connect_args["ssl"] = sslctx
                print("[DEBUG] SSL requested — created ssl.SSLContext and will pass it via connect_args")
            except Exception as e:
                # Print traceback but continue; we'll try without ssl (may fail)
                print("[DEBUG] Failed to create SSL context:", e)
                traceback.print_exc()
        else:
            print("[DEBUG] SSL not requested; connect_args will be empty")

        # Debug: show final connection parameters Alembic will use
        print("[DEBUG] Patched URL for Alembic (ssl/query removed):", patched_url)
        print("[DEBUG] Connect args:", "ssl_context" if "ssl" in connect_args else connect_args)

        # Create async engine (pass connect_args only if not empty)
        try:
            if connect_args:
                connectable: AsyncEngine = create_async_engine(
                    patched_url,
                    poolclass=pool.NullPool,
                    connect_args=connect_args,
                    echo=False,
                )
            else:
                connectable: AsyncEngine = create_async_engine(
                    patched_url,
                    poolclass=pool.NullPool,
                    echo=False,
                )

            async with connectable.begin() as connection:
                # run_migrations will be executed synchronously in the context of the connection
                await connection.run_sync(run_migrations)
        except Exception:
            print("[DEBUG] Exception while creating engine or running migrations:")
            traceback.print_exc()
            raise
        finally:
            # Ensure engine disposed
            try:
                await connectable.dispose()
            except Exception:
                pass

    def run_migrations(connection):
        """Helper to configure Alembic context."""
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(do_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
