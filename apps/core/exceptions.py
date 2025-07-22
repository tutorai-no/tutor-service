from rest_framework.views import exception_handler
from rest_framework.response import Response

class ValidationException(Exception):
    """Custom validation errors."""
    pass

class ServiceException(Exception):
    """Service layer errors."""
    pass

def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses."""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data
        }
        response.data = custom_response_data
    
    return response