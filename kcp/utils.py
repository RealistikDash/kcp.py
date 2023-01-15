from __future__ import annotations

import uuid


def create_unique_token() -> str:
    return str(uuid.uuid4())
