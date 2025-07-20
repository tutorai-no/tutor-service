from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from .views import (
    CourseSectionViewSet,
    CourseViewSet,
    DocumentTagViewSet,
    DocumentViewSet,
)

router = DefaultRouter()
router.register(r"", CourseViewSet, basename="course")

courses_router = routers.NestedDefaultRouter(router, r"", lookup="course")
courses_router.register(r"sections", CourseSectionViewSet, basename="course-sections")
courses_router.register(r"documents", DocumentViewSet, basename="course-documents")

documents_router = routers.NestedDefaultRouter(
    courses_router, r"documents", lookup="document"
)
documents_router.register(r"tags", DocumentTagViewSet, basename="document-tags")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(courses_router.urls)),
    path("", include(documents_router.urls)),
]
