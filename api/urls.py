from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'aksio-backend'})

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('v1/', include('api.v1.urls')),
]