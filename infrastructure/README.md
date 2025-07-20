# Aksio Backend Infrastructure

> Terraform-managed Google Cloud Platform infrastructure for the Aksio educational platform.

## 🏗️ **Quick Overview**

This infrastructure deploys a **serverless, cost-optimized** setup using:
- **Cloud Run** (serverless containers)
- **Cloud SQL PostgreSQL** (managed database)
- **Artifact Registry** (Docker images)
- **Cloud Storage** (static/media files)
- **Secret Manager** (secure secrets)

**Estimated Cost:** $30-60/month for production workloads.

---

## 📁 **File Structure**

```
infrastructure/
├── terraform/
│   ├── cloud-run.tf          # Main infrastructure definition
│   ├── terraform.tfvars      # Environment configuration
│   └── .terraform/           # Terraform state (auto-generated)
└── README.md                 # This file
```

---

## ⚡ **Quick Start**

### **Prerequisites**
```bash
# Install required tools
terraform --version  # >= 1.0
gcloud --version     # Latest
```

### **Deploy Infrastructure**
```bash
cd infrastructure/terraform

# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login
gcloud config set project production-466308

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### **Get Resource Information**
```bash
terraform output
```

---

## 🎯 **Infrastructure Components**

### **Compute**
- **Cloud Run Service**: `aksio-prod-backend`
- **Auto-scaling**: 0-10 instances
- **Resources**: 1 CPU, 1GB RAM per instance
- **Cost**: Pay-per-request only

### **Database**
- **Instance**: `aksio-prod-db` (PostgreSQL 15)
- **Tier**: Custom (1 vCPU, 3.8GB RAM)
- **Storage**: 50GB SSD with auto-resize
- **Backups**: Daily at 2:00 AM, 7-day retention

### **Storage**
- **Static Files**: `aksio-prod-static-*` (CSS, JS, images)
- **Media Files**: `aksio-prod-media-*` (user uploads)
- **Container Images**: `aksio-prod-registry`

### **Security**
- **Service Account**: `aksio-prod-run-sa`
- **Secrets**: Django secret, DB password, OpenAI API key
- **IAM**: Minimal permissions (Cloud SQL, Secret Manager, Storage)

---

## 🔧 **Configuration**

### **Environment Variables**
Edit `terraform.tfvars`:
```hcl
project_id   = "production-466308"
region       = "europe-west1"
environment  = "prod"
domain_name  = "api.aksio.app"
```

### **Scaling Configuration**
In `cloud-run.tf`, adjust:
```hcl
# Auto-scaling limits
"autoscaling.knative.dev/maxScale" = "10"
"autoscaling.knative.dev/minScale" = "0"

# Resource limits
cpu    = "1000m"
memory = "1Gi"
```

---

## 🚀 **Deployment Process**

### **1. Build and Push Docker Image**
```bash
# Build image
docker build -t aksio-backend .

# Tag for registry
IMAGE_URL="europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest"
docker tag aksio-backend $IMAGE_URL

# Push to registry
docker push $IMAGE_URL
```

### **2. Deploy Cloud Run Service**
```bash
# Uncomment Cloud Run service in cloud-run.tf
terraform apply
```

### **3. Set Secrets**
```bash
# Add OpenAI API key
echo "your-api-key" | gcloud secrets versions add aksio-prod-openai-key --data-file=-

# Django secret and DB password are auto-generated
```

---

## 📊 **Monitoring & Management**

### **Check Resource Status**
```bash
# Cloud Run services
gcloud run services list --region=europe-west1

# SQL instances
gcloud sql instances list

# Storage buckets
gcloud storage buckets list

# Secrets
gcloud secrets list
```

### **View Logs**
```bash
# Cloud Run logs
gcloud logs tail --project=production-466308

# Database logs
gcloud sql instances describe aksio-prod-db --format="value(serverCaCert)"
```

### **Database Access**
```bash
# Connect to database
gcloud sql connect aksio-prod-db --user=aksio

# Run migrations
gcloud run jobs execute migrate-job --region=europe-west1
```

---

## 🛡️ **Security Best Practices**

### **Access Control**
- Service account follows **principle of least privilege**
- Database access restricted to Cloud Run only
- Secrets encrypted with Google-managed keys

### **Network Security**
- Database uses private IP when possible
- CORS configured for web security
- HTTPS enforced on all endpoints

### **Backup & Recovery**
- Daily database backups with 7-day retention
- Point-in-time recovery enabled for production
- Infrastructure as Code for disaster recovery

---

## 🔍 **Troubleshooting**

### **Common Issues**

**Cloud Run service fails to start:**
```bash
# Check logs
gcloud logs read --service=aksio-prod-backend --limit=50

# Verify image exists
gcloud artifacts docker images list europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry
```

**Database connection issues:**
```bash
# Check SQL instance status
gcloud sql instances describe aksio-prod-db --format="value(state)"

# Test connectivity
gcloud sql connect aksio-prod-db --user=aksio
```

**Secret access problems:**
```bash
# List secret versions
gcloud secrets versions list aksio-prod-openai-key

# Test secret access
gcloud secrets versions access latest --secret=aksio-prod-openai-key
```

### **Emergency Procedures**

**Scale down to save costs:**
```bash
gcloud run services update aksio-prod-backend \
  --region=europe-west1 \
  --min-instances=0 \
  --max-instances=1
```

**Backup database manually:**
```bash
gcloud sql export sql aksio-prod-db gs://backup-bucket/backup-$(date +%Y%m%d).sql \
  --database=aksio
```

---

## 📝 **Maintenance**

### **Regular Tasks**
- **Weekly**: Review Cloud SQL backup logs
- **Monthly**: Check resource usage and costs
- **Quarterly**: Update Terraform providers and modules

### **Updates**
```bash
# Update Terraform providers
terraform init -upgrade

# Plan and apply changes
terraform plan
terraform apply
```

### **Cost Optimization**
- Monitor unused resources in GCP Console
- Adjust Cloud Run scaling based on traffic
- Review storage bucket lifecycle policies

---

## 🆘 **Support**

### **Resources**
- [Terraform Google Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL PostgreSQL Guide](https://cloud.google.com/sql/docs/postgres)

### **Commands Reference**
See `../docs/gcloud-commands.md` for comprehensive gcloud command reference.

---

## 📋 **Outputs**

After successful deployment, Terraform provides:

```bash
database_connection_name = "production-466308:europe-west1:aksio-prod-db"
database_url = <sensitive>
media_bucket_name = "aksio-prod-media-84df66d5"
registry_url = "europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry"
static_bucket_name = "aksio-prod-static-84df66d5"
```

Use these values for CI/CD configuration and application settings.