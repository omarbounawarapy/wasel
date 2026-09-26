"""The error envelope (01 §4.3 + Skeptic's codes per README R4). The LLM cap never produces an HTTP error."""
from __future__ import annotations


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details

    def body(self) -> dict:
        err = {"code": self.code, "message": self.message}
        if self.details:
            err["details"] = self.details
        return {"error": err}


def not_found(what: str = "order") -> ApiError:
    return ApiError(404, "NOT_FOUND", f"{what} not found")


def seeded_read_only() -> ApiError:
    return ApiError(409, "SEEDED_READ_ONLY", "Sample orders are read-only so every visitor starts from the same "
                                             "point. Try this order to work on your own copy.")


def invalid_transition(allowed: list[str]) -> ApiError:
    return ApiError(409, "INVALID_TRANSITION", "not allowed from the current status", {"allowed": allowed})
