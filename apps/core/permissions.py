from rest_framework.permissions import BasePermission

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