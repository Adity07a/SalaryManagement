"""Application-level exceptions and API error definitions."""


class APIError(Exception):
    """Base application exception with an HTTP-compatible response."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class NotFoundError(APIError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        resource: str,
        resource_id: int,
    ) -> None:
        super().__init__(
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} with ID {resource_id} was not found.",
            details={
                "resource": resource,
                "id": resource_id,
            },
        )


class ConflictError(APIError):
    """Raised when an operation conflicts with existing data."""

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="RESOURCE_CONFLICT",
            message=message,
            details=details,
        )


class DomainValidationError(APIError):
    """Raised when application business rules are violated."""

    def __init__(
        self,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(
            status_code=422,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )
