from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    Course, 
    CourseSection, 
    Document, 
    DocumentTag, 
    DocumentTagAssignment,
    Chat, 
    ChatMessage
)
from .serializers import (
    CourseSerializer, 
    CourseSectionSerializer, 
    DocumentSerializer, 
    DocumentTagSerializer,
    DocumentTagAssignmentSerializer,
    ChatSerializer, 
    ChatMessageSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Course.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CourseSectionViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return CourseSection.objects.filter(course_id=course_id, course__user=self.request.user)
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_pk')
        course = get_object_or_404(Course, id=course_id, user=self.request.user)
        serializer.save(course=course)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return Document.objects.filter(course_id=course_id, course__user=self.request.user)
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_pk')
        course = get_object_or_404(Course, id=course_id, user=self.request.user)
        serializer.save(user=self.request.user, course=course)


class DocumentTagViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentTagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DocumentTag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentTagAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentTagAssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.kwargs.get('document_pk')
        return DocumentTagAssignment.objects.filter(
            document_id=document_id,
            document__user=self.request.user
        )


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        chat_id = self.kwargs.get('chat_pk')
        return ChatMessage.objects.filter(chat_id=chat_id, chat__user=self.request.user)
    
    def perform_create(self, serializer):
        chat_id = self.kwargs.get('chat_pk')
        chat = get_object_or_404(Chat, id=chat_id, user=self.request.user)
        serializer.save(chat=chat)