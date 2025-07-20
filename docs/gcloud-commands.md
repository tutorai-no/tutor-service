# Google Cloud CLI Commands Reference

> Essential gcloud commands for managing Aksio backend infrastructure.

## 🚀 **Quick Setup**

### **Authentication**
```bash
# Login to Google Cloud
gcloud auth login

# Set up application default credentials
gcloud auth application-default login

# Set project
gcloud config set project production-466308

# Verify setup
gcloud config list
gcloud auth list
```

### **Docker Authentication**
```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

---

## 🐳 **Container Management**

### **Artifact Registry**
```bash
# List repositories
gcloud artifacts repositories list

# List images in repository
gcloud artifacts docker images list europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry

# Delete old images (keep latest 5)
gcloud artifacts docker images list europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry \
  --format="value(IMAGE)" | tail -n +6 | xargs -I {} gcloud artifacts docker images delete {} --quiet

# Check repository details
gcloud artifacts repositories describe aksio-prod-registry --location=europe-west1
```

### **Cloud Run**
```bash
# List services
gcloud run services list

# Deploy service
gcloud run deploy aksio-prod-backend \
  --image europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest \
  --region europe-west1 \
  --platform managed

# Update service configuration
gcloud run services update aksio-prod-backend \
  --region europe-west1 \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 1Gi

# Get service URL
gcloud run services describe aksio-prod-backend \
  --region europe-west1 \
  --format="value(status.url)"

# View service details
gcloud run services describe aksio-prod-backend --region europe-west1

# Delete service
gcloud run services delete aksio-prod-backend --region europe-west1
```

---

## 🗄️ **Database Management**

### **Cloud SQL Instances**
```bash
# List instances
gcloud sql instances list

# Instance details
gcloud sql instances describe aksio-prod-db

# Start/stop instance
gcloud sql instances patch aksio-prod-db --activation-policy ALWAYS
gcloud sql instances patch aksio-prod-db --activation-policy NEVER

# Connect to database
gcloud sql connect aksio-prod-db --user=aksio

# Reset root password
gcloud sql users set-password postgres \
  --instance=aksio-prod-db \
  --password=NEW_PASSWORD
```

### **Database Operations**
```bash
# List databases
gcloud sql databases list --instance=aksio-prod-db

# Create database
gcloud sql databases create new_database --instance=aksio-prod-db

# List users
gcloud sql users list --instance=aksio-prod-db

# Create user
gcloud sql users create new_user \
  --instance=aksio-prod-db \
  --password=USER_PASSWORD
```

### **Backups & Exports**
```bash
# List backups
gcloud sql backups list --instance=aksio-prod-db

# Create backup
gcloud sql backups create --instance=aksio-prod-db

# Export database
gcloud sql export sql aksio-prod-db gs://your-bucket/backup.sql \
  --database=aksio

# Import database
gcloud sql import sql aksio-prod-db gs://your-bucket/backup.sql \
  --database=aksio
```

---

## 🔐 **Secret Management**

### **Secret Manager**
```bash
# List secrets
gcloud secrets list

# Create secret
gcloud secrets create new-secret --data-file=secret.txt

# Add secret version
echo "secret-value" | gcloud secrets versions add secret-name --data-file=-

# Access secret
gcloud secrets versions access latest --secret=aksio-prod-openai-key

# List secret versions
gcloud secrets versions list aksio-prod-openai-key

# Delete secret version
gcloud secrets versions destroy 1 --secret=secret-name

# Delete secret
gcloud secrets delete secret-name
```

### **IAM & Service Accounts**
```bash
# List service accounts
gcloud iam service-accounts list

# Create service account
gcloud iam service-accounts create my-service-account \
  --display-name="My Service Account"

# Grant roles to service account
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:my-sa@production-466308.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Create and download service account key
gcloud iam service-accounts keys create key.json \
  --iam-account=my-sa@production-466308.iam.gserviceaccount.com
```

---

## 📦 **Storage Management**

### **Cloud Storage**
```bash
# List buckets
gcloud storage buckets list

# Create bucket
gcloud storage buckets create gs://my-bucket --location=europe-west1

# List files in bucket
gcloud storage ls gs://aksio-prod-static-84df66d5/

# Upload file
gcloud storage cp local-file.txt gs://my-bucket/

# Download file
gcloud storage cp gs://my-bucket/file.txt ./

# Sync directory
gcloud storage rsync ./local-dir gs://my-bucket/remote-dir

# Set bucket permissions
gcloud storage buckets add-iam-policy-binding gs://my-bucket \
  --member=allUsers \
  --role=roles/storage.objectViewer
```

---

## 📊 **Monitoring & Logging**

### **Logs**
```bash
# View Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Follow logs in real-time
gcloud logs tail "resource.type=cloud_run_revision"

# Filter logs by service
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=aksio-prod-backend"

# View Cloud SQL logs
gcloud logs read "resource.type=cloudsql_database" --limit=50

# Export logs
gcloud logs read "resource.type=cloud_run_revision" \
  --format="value(timestamp,severity,textPayload)" > logs.txt
```

### **Metrics & Monitoring**
```bash
# List metrics
gcloud logging metrics list

# Create log-based metric
gcloud logging metrics create error_count \
  --description="Count of error logs" \
  --log-filter='severity="ERROR"'

# View resource usage
gcloud monitoring dashboards list
```

---

## 🔧 **Project & API Management**

### **Project Configuration**
```bash
# List projects
gcloud projects list

# Set active project
gcloud config set project PROJECT_ID

# Get project info
gcloud projects describe production-466308

# List enabled APIs
gcloud services list --enabled

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### **Billing & Quotas**
```bash
# List billing accounts
gcloud billing accounts list

# View quotas
gcloud compute project-info describe --format="value(quotas)"

# Check current usage
gcloud compute instances list
gcloud sql instances list
gcloud run services list
```

---

## 🚨 **Emergency Commands**

### **Quick Scale Down**
```bash
# Scale Cloud Run to minimum
gcloud run services update aksio-prod-backend \
  --region europe-west1 \
  --min-instances 0 \
  --max-instances 1

# Stop SQL instance
gcloud sql instances patch aksio-prod-db --activation-policy NEVER
```

### **Emergency Backup**
```bash
# Quick database backup
DATE=$(date +%Y%m%d-%H%M%S)
gcloud sql export sql aksio-prod-db gs://emergency-backup/backup-$DATE.sql \
  --database=aksio
```

### **Resource Cleanup**
```bash
# Delete Cloud Run service
gcloud run services delete aksio-prod-backend --region europe-west1 --quiet

# Delete SQL instance (dangerous!)
gcloud sql instances delete aksio-prod-db --quiet

# Delete storage bucket
gcloud storage rm -r gs://bucket-name
```

---

## 🔍 **Troubleshooting Commands**

### **Connectivity Tests**
```bash
# Test Cloud Run endpoint
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  https://your-service-url/health

# Test database connectivity
gcloud sql connect aksio-prod-db --user=aksio

# Check DNS resolution
nslookup your-domain.com
```

### **Resource Status**
```bash
# Check all resource states
echo "=== Cloud Run ===" && gcloud run services list
echo "=== Cloud SQL ===" && gcloud sql instances list
echo "=== Storage ===" && gcloud storage buckets list
echo "=== Secrets ===" && gcloud secrets list
```

### **Debug Information**
```bash
# Get detailed error information
gcloud run services describe aksio-prod-backend \
  --region europe-west1 \
  --format="value(status.conditions)"

# Check recent operations
gcloud logging read "protoPayload.serviceName=run.googleapis.com" --limit=10
```

---

## 📋 **Useful Aliases**

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick aliases
alias gcl='gcloud'
alias gcr='gcloud run'
alias gcs='gcloud sql'
alias gcst='gcloud storage'
alias gcp='gcloud config set project'

# Project-specific aliases
alias aksio-logs='gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=aksio-prod-backend"'
alias aksio-deploy='gcloud run deploy aksio-prod-backend --region europe-west1'
alias aksio-db='gcloud sql connect aksio-prod-db --user=aksio'
```

---

## 📚 **Command Templates**

### **Deploy New Version**
```bash
#!/bin/bash
# deploy.sh
IMAGE_TAG="europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:${1:-latest}"

echo "Deploying $IMAGE_TAG..."
gcloud run deploy aksio-prod-backend \
  --image $IMAGE_TAG \
  --region europe-west1 \
  --platform managed

echo "Deployment complete!"
gcloud run services describe aksio-prod-backend \
  --region europe-west1 \
  --format="value(status.url)"
```

### **Database Maintenance**
```bash
#!/bin/bash
# db-backup.sh
DATE=$(date +%Y%m%d)
BUCKET="gs://aksio-backups"

echo "Creating backup for $DATE..."
gcloud sql export sql aksio-prod-db $BUCKET/backup-$DATE.sql \
  --database=aksio

echo "Backup created: $BUCKET/backup-$DATE.sql"
```

---

## 💡 **Tips & Best Practices**

### **Performance**
- Use `--quiet` flag to suppress interactive prompts
- Use `--format` to get specific output fields
- Use `--filter` to reduce API calls

### **Safety**
- Always use `--dry-run` when available
- Test commands in development first
- Keep backups before destructive operations

### **Automation**
- Use service accounts for CI/CD
- Store credentials securely
- Implement retry logic for critical operations

---

This reference covers the most common operations for managing your Aksio backend infrastructure. For detailed options, use `gcloud help COMMAND` or visit the [official documentation](https://cloud.google.com/sdk/gcloud/reference).