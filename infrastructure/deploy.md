# Aksio Backend Deployment Guide

## Simple Cloud Run Deployment (Recommended)

This setup provides a cost-effective deployment using Cloud Run instead of expensive GKE clusters.

### Cost Comparison

**Cloud Run Approach (~$35-95/month):**
- ✅ Cloud Run: ~$5-20/month (pay per request, scales to zero)
- ✅ Cloud SQL (f1-micro): ~$20-30/month
- ✅ Artifact Registry: ~$5-10/month
- ✅ Cloud Storage: ~$5-15/month
- ✅ AuraDB: Variable (external service)

**GKE Approach (~$140-280/month):**
- ❌ GKE cluster: ~$70-100/month minimum
- ❌ Node pools: ~$50-150/month
- ❌ Load balancers: ~$20-30/month

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Terraform** installed (>= 1.0)
3. **gcloud CLI** installed and authenticated
4. **Docker** installed

## Quick Start

### 1. Authenticate with Google Cloud

```bash
# Login to your Google account
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable Application Default Credentials for Terraform
gcloud auth application-default login
```

### 2. Configure Terraform

```bash
cd infrastructure/terraform

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Update `terraform.tfvars`:
```hcl
project_id = "your-actual-project-id"
region = "us-central1"
environment = "prod"
domain_name = "api.aksio.app"
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy the infrastructure
terraform apply
```

### 4. Set up OpenAI API Key

After infrastructure is deployed, add your OpenAI API key to Secret Manager:

```bash
# Get your project ID from terraform output
PROJECT_ID=$(terraform output -raw project_id)

# Add OpenAI API key to Secret Manager
echo "your-openai-api-key" | gcloud secrets versions add aksio-prod-openai-key --data-file=-
```

### 5. Build and Deploy Application

```bash
# Get registry URL from terraform output
REGISTRY_URL=$(terraform output -raw registry_url)

# Build and push Docker image
docker build -f Dockerfile.prod -t ${REGISTRY_URL}/aksio-backend:latest .
docker push ${REGISTRY_URL}/aksio-backend:latest

# Deploy new revision to Cloud Run
gcloud run deploy aksio-prod-backend \
  --image=${REGISTRY_URL}/aksio-backend:latest \
  --region=us-central1 \
  --allow-unauthenticated
```

### 6. Run Database Migrations

```bash
# Get the Cloud Run URL
SERVICE_URL=$(gcloud run services describe aksio-prod-backend --region=us-central1 --format="value(status.url)")

# Run migrations (you may need to add a migration endpoint or use Cloud Run jobs)
gcloud run jobs create aksio-migrate \
  --image=${REGISTRY_URL}/aksio-backend:latest \
  --region=us-central1 \
  --command="python,manage.py,migrate"

gcloud run jobs execute aksio-migrate --region=us-central1
```

## External Services

### AuraDB (Neo4j)

Since you mentioned AuraDB, you'll need to:

1. Create an AuraDB instance at https://console.neo4j.io/
2. Add the connection details to Secret Manager:

```bash
# Add Neo4j connection details
echo "neo4j+s://your-instance.databases.neo4j.io" | gcloud secrets create aksio-prod-neo4j-uri --data-file=-
echo "your-username" | gcloud secrets create aksio-prod-neo4j-user --data-file=-
echo "your-password" | gcloud secrets create aksio-prod-neo4j-password --data-file=-
```

3. Update the Cloud Run service to include these environment variables.

## Monitoring and Logs

```bash
# View Cloud Run logs
gcloud logs read --service=aksio-prod-backend --region=us-central1

# Monitor Cloud Run metrics
gcloud monitoring dashboards list
```

## Scaling and Cost Optimization

### Automatic Scaling
- Cloud Run automatically scales from 0 to 10 instances based on traffic
- You only pay for actual CPU and memory usage
- No charge when service is idle

### Cost Optimization Tips
1. **Use f1-micro for development**: Change `tier` in terraform for non-prod
2. **Enable deletion protection**: Set to `false` for dev/staging environments
3. **Monitor usage**: Use Cloud Monitoring to track costs
4. **Optimize Docker image**: Use multi-stage builds to reduce image size

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   gcloud auth application-default login
   ```

2. **Secret Not Found**:
   ```bash
   gcloud secrets list
   ```

3. **Cloud Run Deploy Fails**:
   ```bash
   gcloud run services logs aksio-prod-backend --region=us-central1
   ```

### Useful Commands

```bash
# Check infrastructure status
terraform refresh && terraform show

# Update Cloud Run service
gcloud run services update aksio-prod-backend --region=us-central1

# Delete everything (careful!)
terraform destroy
```

## CI/CD Integration

The existing `.github/workflows/deploy.yml` can be updated to use Cloud Run instead of the current setup. The workflow already includes:

- ✅ Automated testing
- ✅ Docker image building
- ✅ Artifact Registry push
- ✅ Cloud Run deployment

Just update the workflow to use the new infrastructure resources.

## Next Steps

1. **Set up custom domain**: Configure Cloud DNS and SSL certificates
2. **Add monitoring**: Set up Cloud Monitoring and alerting
3. **Implement backups**: Automate database backups
4. **Security hardening**: Implement IAM best practices
5. **CI/CD pipeline**: Automate deployments with GitHub Actions