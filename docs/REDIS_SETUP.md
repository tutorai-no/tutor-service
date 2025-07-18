# Redis Setup for Production

## Overview

Cloud Run containers are stateless and cannot run Redis internally. You need an external Redis instance for caching and session storage.

## Current Configuration

The production settings are configured to:
1. Use Redis if `REDIS_URL` environment variable is set
2. Fall back to local memory cache if Redis is not available (not recommended for production)

## Option 1: Google Cloud Memorystore (Recommended)

### Create Redis Instance
```bash
# Create a Redis instance
gcloud redis instances create aksio-redis \
  --size=1 \
  --region=europe-west1 \
  --redis-version=redis_7_0 \
  --network=default \
  --project=production-466308

# Get the Redis instance IP
gcloud redis instances describe aksio-redis \
  --region=europe-west1 \
  --format="value(host)"
```

### Configure VPC Connector
Since Cloud Run needs to access Memorystore via private IP, create a VPC connector:

```bash
# Enable required APIs
gcloud services enable vpcaccess.googleapis.com

# Create VPC connector
gcloud compute networks vpc-access connectors create aksio-connector \
  --region=europe-west1 \
  --subnet=default \
  --subnet-project=production-466308 \
  --min-instances=2 \
  --max-instances=10 \
  --machine-type=e2-micro
```

### Update Cloud Run Deployment
Add the VPC connector to your CD workflow:

```yaml
- name: Deploy to Cloud Run
  run: |
    gcloud run deploy ${SERVICE} \
      --vpc-connector=aksio-connector \
      # ... other flags ...
```

### Set Redis URL
Add to GitHub Secrets:
```
REDIS_URL=redis://MEMORYSTORE_IP:6379/0
```

## Option 2: External Redis Provider

Use a managed Redis service with public endpoint:
- **Upstash**: Serverless Redis, pay-per-use
- **Redis Labs**: Free tier available
- **RedisGreen**: Simple pricing

Example with Upstash:
```
REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379
```

## Option 3: Deploy Without Redis (Quick Start)

If you want to deploy immediately without Redis:

1. Don't set `REDIS_URL` in GitHub Secrets
2. The app will use local memory cache
3. Limitations:
   - Cache is not shared between instances
   - Cache is lost when instances restart
   - Sessions won't persist across instances

## Testing Redis Connection

Add this management command to test Redis:

```python
# management/commands/test_redis.py
from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Test Redis connection'

    def handle(self, *args, **options):
        try:
            cache.set('test_key', 'test_value', 60)
            value = cache.get('test_key')
            if value == 'test_value':
                self.stdout.write(self.style.SUCCESS('Redis connection successful!'))
            else:
                self.stdout.write(self.style.ERROR('Redis connection failed: value mismatch'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Redis connection failed: {e}'))
```

## Performance Considerations

1. **With Redis**: 
   - Shared cache across all instances
   - Session persistence
   - Better performance for frequently accessed data

2. **Without Redis**:
   - Each instance has its own cache
   - No session persistence
   - Suitable for stateless operations only

## Monitoring

Monitor Redis performance in Google Cloud Console:
- Memory usage
- Connection count
- Operations per second
- Cache hit ratio