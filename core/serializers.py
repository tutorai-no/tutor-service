from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer that provides common fields and functionality.
    """

    class Meta:
        abstract = True
        read_only_fields = ["id", "created_at", "updated_at"]


class TimestampedSerializer(serializers.ModelSerializer):
    """
    Serializer for models that include timestamp fields.
    """

    class Meta:
        abstract = True
        read_only_fields = ["created_at", "updated_at"]
