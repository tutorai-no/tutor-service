from rest_framework.routers import DefaultRouter

# Create a router for DRF ViewSets
router = DefaultRouter()

# ViewSets will be registered here if needed
# Most apps handle their own routing in their urls.py files

urlpatterns = router.urls