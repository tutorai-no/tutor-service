# Continuous Deployment for Aksio Backend

This document explains the continuous deployment setup that automatically deploys new Docker images from Artifact Registry to Cloud Run.

## Overview

The infrastructure uses **Cloud Build triggers** to automatically deploy when new images are pushed to Artifact Registry. This is the single, unified deployment method for the project.

## How It Works

1. **Push image to Artifact Registry** → 
2. **Cloud Build trigger activates** → 
3. **Runs database migrations** → 
4. **Deploys to Cloud Run**

## Components

### Cloud Run Service (`cloud-run.tf`)

The fully configured Cloud Run service with:
- Auto-scaling (0-10 instances)
- Health checks and startup probes
- Cloud SQL integration
- Secret Manager for sensitive data
- Optimized resource allocation

### Continuous Deployment (`continuous-deployment.tf`)

Cloud Build configuration that:
- Monitors Artifact Registry for new images
- Deploys new revisions without traffic
- Runs database migrations
- Routes traffic after successful migration

## Setup Instructions

### 1. Apply Terraform Configuration

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### 2. Set Required Secrets

```bash
# Django secret key (required)
echo -n "your-very-secure-secret-key" | gcloud secrets versions add aksio-prod-django-secret --data-file=-

# OpenAI API key (required)
echo -n "your-openai-api-key" | gcloud secrets versions add aksio-prod-openai-key --data-file=-
```

### 3. Initial Deployment

Push your first image to trigger deployment:

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Build and tag image
docker build -f config/docker/Dockerfile.prod -t europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-prod-backend:latest .

# Push to trigger deployment
docker push europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-prod-backend:latest
```

## Deployment Process

When you push a new image:

1. **Cloud Build trigger detects the new image**
2. **Deploys to Cloud Run without routing traffic**
3. **Creates a migration job to run database migrations**
4. **Routes traffic to the new revision after success**

## Monitoring Deployments

### View Build Status

```bash
# List recent builds
gcloud builds list --limit=5

# View specific build details
gcloud builds describe [BUILD_ID]

# Stream build logs
gcloud builds log [BUILD_ID] --stream
```

### Check Cloud Run Status

```bash
# View service details
gcloud run services describe aksio-prod-backend --region=europe-west1

# List revisions
gcloud run revisions list --service=aksio-prod-backend --region=europe-west1

# View service logs
gcloud run services logs read aksio-prod-backend --region=europe-west1 --limit=50
```

## Rollback Procedure

If a deployment causes issues:

```bash
# 1. List revisions to find the previous stable version
gcloud run revisions list --service=aksio-prod-backend --region=europe-west1

# 2. Route traffic back to the previous revision
gcloud run services update-traffic aksio-prod-backend \
  --to-revisions=[PREVIOUS_REVISION_NAME]=100 \
  --region=europe-west1

# 3. Optionally, delete the problematic revision
gcloud run revisions delete [BAD_REVISION_NAME] --region=europe-west1
```

## Troubleshooting

### Build Failures

1. **Check build logs**:
   ```bash
   gcloud builds log [BUILD_ID]
   ```

2. **Common issues**:
   - Database migration failures
   - Missing environment variables
   - Insufficient permissions

### Database Migration Issues

- Migrations run as a Cloud Run job
- Check job logs for errors:
  ```bash
  gcloud run jobs list --region=europe-west1
  ```

### Permission Issues

Ensure service accounts have correct roles:
```bash
# Check service account permissions
gcloud projects get-iam-policy [PROJECT_ID] \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:aksio-prod-build-deploy@*"
```

## Disabling Automatic Deployment

To temporarily stop automatic deployments:

```bash
# Disable the trigger
gcloud builds triggers disable aksio-prod-auto-deploy

# Re-enable when ready
gcloud builds triggers enable aksio-prod-auto-deploy
```

## Manual Deployment

If needed, you can still deploy manually:

```bash
gcloud run deploy aksio-prod-backend \
  --image europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-prod-backend:latest \
  --region europe-west1
```

## Best Practices

1. **Tag images properly**: Use semantic versioning (v1.0.0) in addition to 'latest'
2. **Test locally first**: Ensure migrations work before pushing
3. **Monitor deployments**: Set up alerts for failed builds
4. **Keep images small**: Use multi-stage builds to reduce size

## Cost Optimization

- Cloud Run scales to 0 when idle (no charges)
- Cloud Build charges only during build/deploy time
- Delete old revisions to save storage:
  ```bash
  gcloud run revisions delete [OLD_REVISION] --region=europe-west1
  ```

## Security Notes

- Images are automatically scanned for vulnerabilities
- Secrets are never exposed in logs
- Service accounts use minimal required permissions
- All traffic is HTTPS

## Next Steps

1. Set up monitoring alerts for deployment failures
2. Configure deployment notifications (email/Slack)
3. Implement deployment approvals for production
4. Add performance testing to deployment pipeline