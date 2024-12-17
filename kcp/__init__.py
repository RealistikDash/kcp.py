"""Python bindings and abstarctions over the KCP protocol."""
from __future__ import annotations

__description__ = "Python bindings and abstarctions over the KCP protocol."
__version__ = "0.1.6"
__author__ = "RealistikDash <realistikdash@gmail.com>"
__license__ = "MIT"

from .client import KCPClientSync
from .server import Connection
from .server import KCPServerAsync
from .extension import KCP
