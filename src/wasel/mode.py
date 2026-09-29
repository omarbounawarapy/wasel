"""APP_MODE resolution lives in Settings; this module holds the visitor-id dependency."""
from __future__ import annotations

import re

from fastapi import Header, Request

from wasel.api.errors import ApiError

VISITOR_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def visitor_id(x_visitor_id: str | None = Header(default=None)) -> str | None:
    """The header is not signed and is not identity. Anything malformed counts as no visitor."""
    return x_visitor_id if x_visitor_id and VISITOR_RE.match(x_visitor_id) else None


def require_visitor(request: Request, vid: str | None) -> str | None:
    """Public-mode mutations need a visitor id (400 VISITOR_ID_REQUIRED otherwise). Ignored in event/dev."""
    if request.app.state.core.settings.is_public and vid is None:
        raise ApiError(400, "VISITOR_ID_REQUIRED", "X-Visitor-Id (uuid v4) is required in the public demo",
                       {"X-Visitor-Id": ["missing or malformed"]})
    return vid
