from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.swagger_utils import swagger_tag

from .models import Invoice, Payment, Plan, Subscription
from .serializers import (
    InvoiceSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)


@swagger_tag("Billing")
class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True)


@swagger_tag("Billing")
class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle schema generation
        if getattr(self, "swagger_fake_view", False):
            return Subscription.objects.none()
        return Subscription.objects.filter(user=self.request.user)


@swagger_tag("Billing")
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle schema generation
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        return Payment.objects.filter(user=self.request.user)


@swagger_tag("Billing")
class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle schema generation
        if getattr(self, "swagger_fake_view", False):
            return Invoice.objects.none()
        return Invoice.objects.filter(user=self.request.user)
