"""Python bindings and abstarctions over the KCP protocol."""

from __future__ import annotations

__description__ = "Python bindings and abstarctions over the KCP protocol."
__version__ = "1.0.0"
__author__ = "RealistikDash <realistikdash@gmail.com>"
__license__ = "MIT"

from .client import KCPClientSync
from .extension import KCP
from .server import Connection
from .server import KCPServerAsync

__all__ = [
    "KCP",
    "Connection",
    "KCPClientSync",
    "KCPServerAsync",
]
