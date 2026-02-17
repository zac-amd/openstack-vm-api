"""Custom exception classes for the API."""

from typing import Any, Optional


class APIException(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize API exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class AuthenticationException(APIException):
    """Exception for authentication failures."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize authentication exception."""
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationException(APIException):
    """Exception for authorization failures."""

    def __init__(
        self,
        message: str = "Not authorized to perform this action",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize authorization exception."""
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class VMNotFoundException(APIException):
    """Exception when VM is not found."""

    def __init__(
        self,
        vm_id: str,
        message: Optional[str] = None,
    ) -> None:
        """Initialize VM not found exception."""
        super().__init__(
            message=message or f"VM with ID '{vm_id}' not found",
            status_code=404,
            error_code="VM_NOT_FOUND",
            details={"vm_id": vm_id},
        )


class VMStateException(APIException):
    """Exception for invalid VM state transitions."""

    def __init__(
        self,
        vm_id: str,
        current_state: str,
        action: str,
        message: Optional[str] = None,
    ) -> None:
        """Initialize VM state exception."""
        default_message = (
            f"Cannot perform '{action}' on VM '{vm_id}' in state '{current_state}'"
        )
        super().__init__(
            message=message or default_message,
            status_code=409,
            error_code="INVALID_VM_STATE",
            details={
                "vm_id": vm_id,
                "current_state": current_state,
                "requested_action": action,
            },
        )


class VMAlreadyExistsException(APIException):
    """Exception when VM already exists."""

    def __init__(
        self,
        name: str,
        message: Optional[str] = None,
    ) -> None:
        """Initialize VM already exists exception."""
        super().__init__(
            message=message or f"VM with name '{name}' already exists",
            status_code=409,
            error_code="VM_ALREADY_EXISTS",
            details={"name": name},
        )


class OpenStackException(APIException):
    """Exception for OpenStack API errors."""

    def __init__(
        self,
        message: str,
        openstack_error: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize OpenStack exception."""
        error_details = details or {}
        if openstack_error:
            error_details["openstack_error"] = openstack_error

        super().__init__(
            message=message,
            status_code=502,
            error_code="OPENSTACK_ERROR",
            details=error_details,
        )


class OpenStackConnectionException(OpenStackException):
    """Exception for OpenStack connection failures."""

    def __init__(
        self,
        message: str = "Failed to connect to OpenStack",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize OpenStack connection exception."""
        super().__init__(
            message=message,
            details=details,
        )
        self.error_code = "OPENSTACK_CONNECTION_ERROR"
        self.status_code = 503


class ResourceNotFoundException(APIException):
    """Exception when a resource (flavor, image, etc.) is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
    ) -> None:
        """Initialize resource not found exception."""
        super().__init__(
            message=message or f"{resource_type} with ID '{resource_id}' not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class ValidationException(APIException):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize validation exception."""
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )
