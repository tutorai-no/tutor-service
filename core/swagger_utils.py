"""
Swagger/OpenAPI utilities for consistent API documentation.
"""

from drf_yasg.utils import swagger_auto_schema


def swagger_tag(*tags):
    """
    Decorator to add tags to all methods of a ViewSet.

    Usage:
        @swagger_tag('MyApp')
        class MyViewSet(viewsets.ModelViewSet):
            ...
    """

    def decorator(cls):
        # Standard ViewSet methods
        methods = ["list", "create", "retrieve", "update", "partial_update", "destroy"]

        for method in methods:
            if hasattr(cls, method):
                # Apply swagger_auto_schema decorator directly to the method
                original_method = getattr(cls, method)
                # Check if method already has swagger data
                if not hasattr(original_method, "_swagger_auto_schema"):
                    decorated_method = swagger_auto_schema(tags=list(tags))(
                        original_method
                    )
                    setattr(cls, method, decorated_method)

        # Also decorate any custom actions
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if hasattr(attr, "mapping"):  # It's an action
                # Check if action already has swagger data
                if not hasattr(attr, "_swagger_auto_schema"):
                    setattr(cls, attr_name, swagger_auto_schema(tags=list(tags))(attr))

        return cls

    return decorator
