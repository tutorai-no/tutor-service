# Minimal Development Setup

This guide helps you run the Aksio backend with ALL features enabled while using minimal infrastructure resources.

## What's Different

The minimal setup provides full backend functionality by:
- **Including Neo4j** for real knowledge graph capabilities
- **Removing Redis** and using in-memory caching instead
- **Running background tasks synchronously** instead of with separate workers

### Infrastructure Changes:
- **Redis** → Django's in-memory cache (LocMemCache)
- **Kafka & Zookeeper** → Not needed (already disabled)
- **Celery Workers** → Tasks run synchronously (CELERY_TASK_ALWAYS_EAGER)
- **Monitoring Tools** → PGAdmin, Redis Commander removed
- **Neo4j** → Included with optimized memory settings

### Features Included:
- ✅ **All AI Features** - Full OpenAI integration
- ✅ **Document Processing** - All processing capabilities
- ✅ **Real-time Chat** - WebSocket support
- ✅ **Background Tasks** - Run inline instead of async
- ✅ **Knowledge Graph** - Full Neo4j capabilities

## Quick Start

### Option 1: Use the Minimal Docker Compose

```bash
# Use the minimal configuration
docker-compose -f docker-compose.minimal.yaml up -d

# Check services (only backend, postgres, redis)
docker-compose -f docker-compose.minimal.yaml ps

# View logs
docker-compose -f docker-compose.minimal.yaml logs -f backend
```

### Option 2: Use Regular Compose with Minimal Environment

```bash
# Copy minimal environment settings
cp .env.minimal .env

# Start services (this will start backend, db, and neo4j)
docker-compose -f docker-compose.minimal.yaml up -d

# Redis and monitoring tools won't start
```

## Resource Usage Comparison

### Full Setup
- **Services**: 6+ containers (backend, postgres, redis, neo4j, kafka, zookeeper)
- **Memory**: ~4-6 GB
- **CPU**: High usage with all services
- **Disk**: ~2-3 GB for all images

### Minimal Setup
- **Services**: 3 containers (backend, postgres, neo4j)
- **Memory**: ~2-3 GB (Neo4j optimized for 1.5GB)
- **CPU**: Moderate usage
- **Disk**: ~1.5 GB for images
- **Features**: ALL features enabled with real knowledge graph!

## Configuration Details

### AI Features (Enabled)
The minimal setup includes full AI functionality:
```bash
# Required in .env
OPENAI_API_KEY=your-actual-api-key
```

### Neo4j Configuration
Neo4j is included with optimized memory settings:
```bash
# Automatically configured for minimal memory usage
NEO4J_server_memory_heap_max__size=1G
NEO4J_server_memory_pagecache__size=512m
```

Access Neo4j Browser at: http://localhost:7474

### Celery Tasks (Synchronous)
Background tasks run immediately instead of queuing:
```bash
# Automatically configured
CELERY_TASK_ALWAYS_EAGER=True
CELERY_TASK_EAGER_PROPAGATES=True
```

This means:
- Email sending happens immediately
- Document processing runs inline
- No separate worker processes needed

## Development Commands

```bash
# Run migrations
docker-compose -f docker-compose.minimal.yaml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.minimal.yaml exec backend python manage.py createsuperuser

# Run tests
docker-compose -f docker-compose.minimal.yaml exec backend python manage.py test

# Access Django shell
docker-compose -f docker-compose.minimal.yaml exec backend python manage.py shell
```

## Troubleshooting

### If services fail to start
1. Check available memory: `docker system df`
2. Clean up Docker: `docker system prune -a`
3. Restart Docker Desktop/daemon

### If AI features don't work
1. Ensure OPENAI_API_KEY is set in .env
2. Check the API key is valid
3. Monitor logs: `docker-compose -f docker-compose.minimal.yaml logs backend`

### If caching issues occur
The minimal setup uses Django's in-memory cache. This means:
1. Cache is not shared between container restarts
2. No cache persistence
3. For production, consider adding Redis back

### Database connection issues
The minimal setup uses a tuned PostgreSQL configuration for lower memory usage. If you experience issues:
```bash
# Connect to database
docker-compose -f docker-compose.minimal.yaml exec db psql -U aksio_user -d aksio_db

# Check connections
SELECT count(*) FROM pg_stat_activity;
```

## Performance Tips

1. **Disable unnecessary features**: Keep ENABLE_* flags False unless needed
2. **Use Alpine images**: The minimal setup uses Alpine Linux variants
3. **Limit Django workers**: The minimal setup runs with a single worker
4. **Disable Redis persistence**: Saves disk I/O in development

## Switching Back to Full Setup

To switch back to the full development environment:
```bash
# Stop minimal containers
docker-compose -f docker-compose.minimal.yaml down

# Use regular docker-compose
docker-compose up -d
```