from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status


class BaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that provides common functionality.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Override to filter by user by default.
        """
        queryset = super().get_queryset()
        
        # Filter by user if the model has a user field
        if hasattr(self.queryset.model, 'user'):
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Override to set user field during creation.
        """
        # Set user field if the model has one
        if hasattr(serializer.Meta.model, 'user'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class ReadOnlyBaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base Read-only ViewSet that provides common functionality.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Override to filter by user by default.
        """
        queryset = super().get_queryset()
        
        # Filter by user if the model has a user field
        if hasattr(self.queryset.model, 'user'):
            queryset = queryset.filter(user=self.request.user)
        
        return queryset