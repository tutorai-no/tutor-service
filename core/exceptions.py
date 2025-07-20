import logging

from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class AksioException(Exception):
    """
    Base exception for Aksio-specific errors.
    """


class CourseNotFound(AksioException):
    """
    Exception raised when a course is not found.
    """


class InsufficientPermissions(AksioException):
    """
    Exception raised when user doesn't have sufficient permissions.
    """


class InvalidOperation(AksioException):
    """
    Exception raised when an invalid operation is attempted.
    """


def custom_exception_handler(exc, context):
    """
    Custom exception handler for the API.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If this is a known exception, return a custom response
    if response is not None:
        custom_response_data = {
            "error": True,
            "message": "An error occurred",
            "details": response.data,
        }

        # Log the error
        logger.error(f"API Error: {exc}", exc_info=True)

        response.data = custom_response_data

    # Handle Django validation errors
    elif isinstance(exc, ValidationError):
        custom_response_data = {
            "error": True,
            "message": "Validation error",
            "details": exc.message_dict if hasattr(exc, "message_dict") else str(exc),
        }

        logger.error(f"Validation Error: {exc}", exc_info=True)

        response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)

    # Handle 404 errors
    elif isinstance(exc, Http404):
        custom_response_data = {
            "error": True,
            "message": "Resource not found",
            "details": str(exc),
        }

        response = Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)

    # Handle custom Aksio exceptions
    elif isinstance(exc, AksioException):
        custom_response_data = {"error": True, "message": str(exc), "details": None}

        logger.error(f"Aksio Error: {exc}", exc_info=True)

        if isinstance(exc, CourseNotFound):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, InsufficientPermissions):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, InvalidOperation):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        response = Response(custom_response_data, status=status_code)

    return response
