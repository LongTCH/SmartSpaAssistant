"""
Custom Exception Classes for the Application

This module contains custom exception classes that provide specific error handling
for different scenarios in the application.
"""

from typing import Any, Dict, Optional

from fastapi import status


class BaseCustomException(Exception):
    """Base custom exception class with common attributes"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class ValidationException(BaseCustomException):
    """Exception for validation errors"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )
        if field:
            self.details["field"] = field


class NotFoundError(BaseCustomException):
    """Exception for resource not found errors"""

    def __init__(
        self,
        resource: str,
        identifier: Any = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"

        super().__init__(
            message=message, status_code=status.HTTP_404_NOT_FOUND, details=details
        )
        self.details.update({"resource": resource, "identifier": identifier})


class UnauthorizedError(BaseCustomException):
    """Exception for unauthorized access"""

    def __init__(
        self,
        message: str = "Unauthorized access",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details
        )


class ForbiddenError(BaseCustomException):
    """Exception for forbidden access"""

    def __init__(
        self,
        message: str = "Access forbidden",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_403_FORBIDDEN, details=details
        )


class ConflictError(BaseCustomException):
    """Exception for resource conflicts"""

    def __init__(
        self,
        message: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_409_CONFLICT, details=details
        )
        if resource:
            self.details["resource"] = resource


class BadRequestError(BaseCustomException):
    """Exception for bad request errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )


class ExternalServiceError(BaseCustomException):
    """Exception for external service errors"""

    def __init__(
        self,
        service_name: str,
        message: str = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"Error communicating with {service_name}"
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )
        self.details["service"] = service_name


class DatabaseError(BaseCustomException):
    """Exception for database-related errors"""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class FileProcessingError(BaseCustomException):
    """Exception for file processing errors"""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )
        if filename:
            self.details["filename"] = filename


class RateLimitError(BaseCustomException):
    """Exception for rate limiting"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )
        if retry_after:
            self.details["retry_after"] = retry_after


class ConfigurationError(BaseCustomException):
    """Exception for configuration errors"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )
        if config_key:
            self.details["config_key"] = config_key


# Business Logic Specific Exceptions


class GuestError(BaseCustomException):
    """Exception for guest-related errors"""

    def __init__(
        self,
        message: str,
        guest_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )
        if guest_id:
            self.details["guest_id"] = guest_id


class ChatError(BaseCustomException):
    """Exception for chat-related errors"""

    def __init__(
        self,
        message: str,
        chat_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )
        if chat_id:
            self.details["chat_id"] = chat_id


class ScriptError(BaseCustomException):
    """Exception for script-related errors"""

    def __init__(
        self,
        message: str,
        script_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )
        if script_id:
            self.details["script_id"] = script_id


class InterestError(BaseCustomException):
    """Exception for interest-related errors"""

    def __init__(
        self,
        message: str,
        interest_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )
        if interest_id:
            self.details["interest_id"] = interest_id


class SheetError(BaseCustomException):
    """Exception for sheet-related errors"""

    def __init__(
        self,
        message: str,
        sheet_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )
        if sheet_id:
            self.details["sheet_id"] = sheet_id


class NotificationError(BaseCustomException):
    """Exception for notification-related errors"""

    def __init__(
        self,
        message: str,
        notification_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details
        )
        if notification_id:
            self.details["notification_id"] = notification_id
