from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import NotAuthenticated


class IsAuthenticatedOrError(IsAuthenticated):
    """
    Custom permission that raises 401 instead of returning False.
    This ensures we get 401 errors instead of 403 for unauthenticated requests.
    """
    
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        raise NotAuthenticated()


class IsOwnerOrReadOnly(BasePermission):
    """Users can edit their own content, read others."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.user == request.user

class IsAdminOrReadOnly(BasePermission):
    """Admin can edit, users can only read."""
    
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.is_staff