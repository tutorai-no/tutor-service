from django.utils.text import slugify
import uuid

def generate_unique_slug(title, model_class, field_name='slug'):
    """Generate unique slug for models."""
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    
    while model_class.objects.filter(**{field_name: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

def build_api_response(data=None, message=None, status='success'):
    """Standardized API response format."""
    return {
        'status': status,
        'message': message,
        'data': data
    }