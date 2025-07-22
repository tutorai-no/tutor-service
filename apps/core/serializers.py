from rest_framework import serializers

class TimestampedModelSerializer(serializers.ModelSerializer):
    """Base serializer for timestamped models."""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)