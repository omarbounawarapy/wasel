"""The API error envelope. The LLM cap never produces an HTTP error."""
from __future__ import annotations


class ApiError(Exception):
    """An error that the app turns into `{"error": {"code", "message", "details"?}}` with HTTP `status`."""

    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details

    def body(self) -> dict:
        """The JSON error envelope; `details` is included only when non-empty."""
        err = {"code": self.code, "message": self.message}
        if self.details:
            err["details"] = self.details
        return {"error": err}


def not_found(what: str = "order") -> ApiError:
    """404. Also used for rows owned by another visitor, so their existence is not revealed."""
    return ApiError(404, "NOT_FOUND", f"{what} not found")


def seeded_read_only() -> ApiError:
    """409: mutation attempted on a sample order in public mode."""
    return ApiError(409, "SEEDED_READ_ONLY", "Sample orders are read-only so every visitor starts from the same "
                                             "point. Try this order to work on your own copy.")


def invalid_transition(allowed: list[str]) -> ApiError:
    """409. `allowed` lists the seller actions valid from the order's current status."""
    return ApiError(409, "INVALID_TRANSITION", "not allowed from the current status", {"allowed": allowed})


# Request bodies that are a union discriminated by `kind`, keyed by the model name pydantic puts in the error path.
UNION_KINDS = {"PasteIngest": "paste", "CsvIngest": "csv", "SimulateText": "text", "SimulateLocation": "location"}


def validation_details(errors: list[dict]) -> tuple[str, dict[str, list[str]]]:
    """Turn pydantic errors into `(message, details)`.

    A union body is validated against every model, so a body with the wrong or missing `kind` fails all of them.
    Without `kind` this returns one sentence naming the accepted values; with a valid `kind` only the errors of
    the matching model are kept, without the model name in the path.
    """
    groups: dict[str, list[dict]] = {}
    for err in errors:
        model = err["loc"][1] if len(err["loc"]) > 2 and err["loc"][1] in UNION_KINDS else None
        groups.setdefault(model, []).append(err)
    models = [m for m in groups if m]
    if models:
        matched = [m for m in models if not any(e["loc"][-1] == "kind" for e in groups[m])]
        if matched:
            errors = groups.get(None, []) + groups[matched[0]]
        else:
            kinds = " or ".join(f'"{UNION_KINDS[m]}"' for m in models)
            return f"kind must be {kinds}", {}
    details: dict[str, list[str]] = {}
    for err in errors:
        loc = [x for x in err["loc"][1:] if x not in UNION_KINDS]
        details.setdefault(".".join(str(x) for x in loc) or "body", []).append(err["msg"])
    return "invalid request", details
