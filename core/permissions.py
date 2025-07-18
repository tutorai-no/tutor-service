from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # All permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsCourseOwner(permissions.BasePermission):
    """
    Custom permission to only allow course owners to access course-related objects.
    """

    def has_object_permission(self, request, view, obj):
        # Check if object has a course field
        if hasattr(obj, 'course'):
            return obj.course.owner == request.user
        return False