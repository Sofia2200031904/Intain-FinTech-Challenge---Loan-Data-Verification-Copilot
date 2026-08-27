"""Canonical ASGI entrypoint.

The project uses MongoDB exclusively. Keeping this module allows conventional
commands such as ``uvicorn app.main:app`` without maintaining a second backend.
"""

from .mongo_main import app

__all__ = ["app"]
