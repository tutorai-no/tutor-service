from rest_framework import permissions


class CourseOwnerPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of a course to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user,
        # only if they own the course
        return obj.owner == request.user
