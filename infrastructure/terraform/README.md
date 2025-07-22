# Aksio Backend Infrastructure

This directory contains Terraform configurations for deploying the Aksio backend to Google Cloud Platform.

## Overview

The infrastructure includes:
- **Cloud Run** service for the Django application
- **Cloud SQL** PostgreSQL database
- **Artifact Registry** for Docker images
- **Cloud Storage** buckets for static and media files
- **Secret Manager** for sensitive configuration
- **Continuous Deployment** via Cloud Build triggers

## Prerequisites

1. Google Cloud Project with billing enabled
2. Terraform installed (>= 1.0)
3. `gcloud` CLI configured with appropriate permissions
4. Docker for building images

## Quick Start

### 1. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### 2. Configure Variables

Create a `terraform.tfvars` file:

```hcl
project_id  = "your-project-id"
region      = "europe-west1"
environment = "prod"
domain_name = "api.yourdomain.com"
```

### 3. Apply Infrastructure

```bash
terraform plan
terraform apply
```

### 4. Set Secrets

After infrastructure is created:

```bash
# Set Django secret key (REQUIRED)
echo -n "your-very-secure-secret-key" | gcloud secrets versions add aksio-prod-django-secret --data-file=-

# Set OpenAI API key (REQUIRED)
echo -n "your-openai-api-key" | gcloud secrets versions add aksio-prod-openai-key --data-file=-
```

## Continuous Deployment

The infrastructure includes automatic deployment via Cloud Build triggers:

- **Trigger**: New images pushed to Artifact Registry
- **Process**: Deploy → Migrate → Route traffic
- **Rollback**: Automatic revision management

See [CONTINUOUS_DEPLOYMENT.md](./CONTINUOUS_DEPLOYMENT.md) for detailed documentation.

## First Deployment

Since Cloud Run requires an image to exist:

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Get registry URL
REGISTRY=$(terraform output -raw registry_url)

# Build and push
docker build -f config/docker/Dockerfile.prod -t $REGISTRY/aksio-prod-backend:latest .
docker push $REGISTRY/aksio-prod-backend:latest
```

The deployment will automatically trigger when the image is pushed.

## Infrastructure Components

### Cloud Run (`cloud-run.tf`)
- Fully managed serverless container platform
- Auto-scaling from 0 to 10 instances
- Health checks and startup probes
- Integrated with Cloud SQL and Secret Manager

### Cloud SQL (`cloud-run.tf`)
- PostgreSQL 15 database
- Automated backups (7 days retention)
- Point-in-time recovery (production only)
- Private IP with Cloud SQL proxy

### Artifact Registry (`cloud-run.tf`)
- Docker container registry
- Vulnerability scanning
- Integration with Cloud Build

### Cloud Build (`continuous-deployment.tf`)
- Automatic triggers on image push
- Database migration handling
- Blue-green deployment strategy

### Storage (`cloud-run.tf`)
- Static files bucket (Whitenoise integration)
- Media files bucket (optional)
- CORS configured for web access

### Secret Manager (`cloud-run.tf`)
- Django secret key storage
- API keys management
- Automatic secret rotation support

## Monitoring

### View Deployments
```bash
gcloud builds list --limit=10
```

### Check Service Status
```bash
gcloud run services describe aksio-prod-backend --region europe-west1
```

### View Logs
```bash
gcloud run services logs read aksio-prod-backend --region europe-west1 --limit=50
```

## Cost Optimization

1. **Cloud Run**: Scales to zero - no charges when idle
2. **Cloud SQL**: Use `db-f1-micro` for development
3. **Storage**: Enable lifecycle policies for old files
4. **Builds**: Clean up old build logs periodically

## Security

- All secrets in Secret Manager
- Service accounts with minimal permissions
- Automatic vulnerability scanning
- HTTPS only with managed certificates
- Cloud SQL private IP connectivity

## Troubleshooting

### Common Issues

1. **First deployment fails**: Ensure image exists in Artifact Registry
2. **Database connection errors**: Check Cloud SQL proxy configuration
3. **Secret access denied**: Verify service account permissions
4. **Build trigger not working**: Check Cloud Build API is enabled

### Debug Commands

```bash
# Check build logs
gcloud builds log [BUILD_ID]

# Describe service
gcloud run services describe aksio-prod-backend --region europe-west1

# Check permissions
gcloud projects get-iam-policy [PROJECT_ID]
```

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy
```

**⚠️ WARNING**: This permanently deletes:
- All databases and data
- Storage buckets and files
- Secrets and configurations
- The Cloud Run service

## Support

For issues or questions:
1. Check [CONTINUOUS_DEPLOYMENT.md](./CONTINUOUS_DEPLOYMENT.md)
2. Review Cloud Build logs
3. Verify all secrets are set correctly
4. Ensure APIs are enabled