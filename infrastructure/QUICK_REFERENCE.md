# Infrastructure Quick Reference

> Essential commands for daily operations.

## 🚀 **Deploy Infrastructure**
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

## 🐳 **Deploy Application**
```bash
# Build and push
docker build -t aksio-backend .
docker tag aksio-backend europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest
docker push europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest

# Deploy via Cloud Run
gcloud run deploy aksio-prod-backend \
  --image europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest \
  --region europe-west1
```

## 🔐 **Manage Secrets**
```bash
# Add OpenAI key
echo "your-api-key" | gcloud secrets versions add aksio-prod-openai-key --data-file=-

# View secret
gcloud secrets versions access latest --secret=aksio-prod-openai-key
```

## 📊 **Monitor Resources**
```bash
# Check status
gcloud run services list
gcloud sql instances list
gcloud storage buckets list

# View logs
gcloud logs tail "resource.type=cloud_run_revision"
```

## 🗄️ **Database Operations**
```bash
# Connect
gcloud sql connect aksio-prod-db --user=aksio

# Backup
gcloud sql export sql aksio-prod-db gs://backup-bucket/backup-$(date +%Y%m%d).sql --database=aksio
```

## 🚨 **Emergency**
```bash
# Scale down
gcloud run services update aksio-prod-backend --region europe-west1 --min-instances 0 --max-instances 1

# Stop database
gcloud sql instances patch aksio-prod-db --activation-policy NEVER
```

## 📋 **Outputs**
```bash
terraform output
```

**Key URLs:**
- Registry: `europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry`
- Database: `production-466308:europe-west1:aksio-prod-db`
- Buckets: `aksio-prod-static-*`, `aksio-prod-media-*`