# Aksio Backend Documentation

> Comprehensive documentation for the Aksio educational platform backend.

## 📚 **Documentation Index**

### **🏗️ Infrastructure**
- **[Infrastructure Setup](../infrastructure/README.md)** - Terraform-managed GCP infrastructure
- **[gcloud Commands Reference](./gcloud-commands.md)** - Essential Google Cloud CLI commands

### **🔧 Setup & Configuration**
- **[Repository Structure](./REPOSITORY_STRUCTURE.md)** - Project organization and architecture
- **[Workload Identity Setup](./WORKLOAD_IDENTITY_SETUP.md)** - GitHub Actions authentication
- **[Redis Setup](./REDIS_SETUP.md)** - Redis configuration and usage

---

## 🚀 **Quick Start Guide**

### **1. Infrastructure Deployment**
```bash
# Clone repository
git clone <repository-url>
cd aksio-backend

# Deploy infrastructure
cd infrastructure/terraform
terraform init
terraform apply

# Note the outputs for next steps
terraform output
```

### **2. Application Deployment**
```bash
# Build and push Docker image
docker build -t aksio-backend .
docker tag aksio-backend europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest
docker push europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:latest

# Deploy to Cloud Run (automated via GitHub Actions)
git push origin main
```

### **3. Environment Configuration**
```bash
# Set required secrets
echo "your-openai-key" | gcloud secrets versions add aksio-prod-openai-key --data-file=-

# Configure domain (optional)
gcloud run domain-mappings create --service aksio-prod-backend --domain api.aksio.app
```

---

## 📋 **Architecture Overview**

### **Technology Stack**
- **Backend**: Django 5.1.11 with Django REST Framework
- **Database**: PostgreSQL 15 (Cloud SQL)
- **Compute**: Google Cloud Run (serverless containers)
- **Storage**: Google Cloud Storage (static files, media)
- **Registry**: Google Artifact Registry (Docker images)
- **Secrets**: Google Secret Manager
- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform

### **Service Architecture**
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Frontend      │────│  Cloud Run   │────│  Cloud SQL      │
│   (External)    │    │  (Django)    │    │  (PostgreSQL)   │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
            ┌───────────────┐   ┌──────────────┐
            │ Cloud Storage │   │Secret Manager│
            │ (Files)       │   │ (API Keys)   │
            └───────────────┘   └──────────────┘
```

### **Microservices Boundaries**
- **aksio-backend** (this repo): Core business logic, user management, learning features
- **retrieval-service** (external): Document processing, RAG system, embeddings
- **Frontend applications** (external): Web and mobile clients

---

## 🔐 **Security & Authentication**

### **Service Authentication**
- **GitHub Actions**: Workload Identity Federation (no service account keys)
- **Cloud Run**: Service account with minimal permissions
- **Inter-service**: OAuth 2.0 and API keys

### **Secret Management**
- **API Keys**: Google Secret Manager
- **Database Credentials**: Auto-generated and encrypted
- **Environment Variables**: Injected securely at runtime

### **Network Security**
- **HTTPS Only**: All endpoints enforce TLS
- **CORS**: Configured for web security
- **Database**: Private network access when possible

---

## 💰 **Cost Management**

### **Current Infrastructure Costs**
- **Cloud Run**: $0 when idle, scales with usage
- **Cloud SQL**: ~$25-50/month (custom-1-3840 tier)
- **Storage**: ~$1-5/month (depends on usage)
- **Artifact Registry**: ~$0.10/GB/month
- **Secret Manager**: ~$0.06 per 10,000 operations

**Total Estimated: $30-60/month for production workloads**

### **Cost Optimization**
- **Serverless First**: Pay only for actual usage
- **Auto-scaling**: Scales to zero during idle periods
- **Resource Right-sizing**: Optimized for workload requirements
- **Lifecycle Policies**: Automatic cleanup of old artifacts

---

## 🔍 **Monitoring & Observability**

### **Logging**
```bash
# Application logs
gcloud logs tail "resource.type=cloud_run_revision"

# Database logs
gcloud logs tail "resource.type=cloudsql_database"

# Infrastructure logs
gcloud logs tail "resource.type=gce_instance"
```

### **Metrics**
- **Response Time**: Cloud Run request latency
- **Error Rate**: HTTP 5xx responses
- **Database Performance**: Connection pool, query time
- **Resource Usage**: CPU, memory, disk utilization

### **Health Checks**
- **Application**: `/api/health/` endpoint
- **Database**: Connection testing
- **External Services**: Dependency health checks

---

## 🚨 **Troubleshooting**

### **Common Issues**

**Service won't start:**
1. Check Docker image exists in Artifact Registry
2. Verify environment variables are set
3. Check service account permissions
4. Review Cloud Run logs

**Database connection failures:**
1. Verify Cloud SQL instance is running
2. Check connection string format
3. Validate database user permissions
4. Test network connectivity

**CI/CD pipeline failures:**
1. Check Workload Identity Federation setup
2. Verify repository permissions in Artifact Registry
3. Validate environment secrets in GitHub
4. Review GitHub Actions logs

### **Emergency Procedures**

**Scale down for cost savings:**
```bash
gcloud run services update aksio-prod-backend \
  --region europe-west1 \
  --min-instances 0 \
  --max-instances 1
```

**Emergency database backup:**
```bash
DATE=$(date +%Y%m%d-%H%M%S)
gcloud sql export sql aksio-prod-db gs://emergency-backup/backup-$DATE.sql
```

**Rollback deployment:**
```bash
# Deploy previous image
gcloud run deploy aksio-prod-backend \
  --image europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry/aksio-backend:previous-tag
```

---

## 🔧 **Development Workflow**

### **Local Development**
1. **Setup**: `docker-compose up -d` (database, redis)
2. **Install**: `pip install -r requirements/dev.txt`
3. **Migrate**: `python manage.py migrate`
4. **Run**: `python manage.py runserver`

### **Testing**
```bash
# Run tests
python manage.py test

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### **Deployment Pipeline**
1. **Push to branch** → Triggers CI (tests, build)
2. **CI success** → Triggers CD (deploy)
3. **Deployment** → Automatic health checks
4. **Monitoring** → Continuous observability

---

## 📞 **Support & Resources**

### **Internal Documentation**
- **[Infrastructure README](../infrastructure/README.md)** - Detailed infrastructure setup
- **[gcloud Commands](./gcloud-commands.md)** - Command reference guide
- **[Repository Structure](./REPOSITORY_STRUCTURE.md)** - Codebase organization

### **External Resources**
- **[Google Cloud Documentation](https://cloud.google.com/docs)**
- **[Django Documentation](https://docs.djangoproject.com/)**
- **[Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)**

### **Emergency Contacts**
- **Infrastructure Issues**: DevOps team
- **Application Issues**: Backend development team
- **Security Incidents**: Security team

---

## 🎯 **Next Steps**

### **Immediate**
1. Set up monitoring and alerting
2. Configure custom domain
3. Implement automated backups
4. Set up staging environment

### **Medium Term**
1. Add Redis for caching
2. Implement CDN for static files
3. Set up load testing
4. Add more comprehensive logging

### **Long Term**
1. Multi-region deployment
2. Advanced monitoring and alerting
3. Disaster recovery procedures
4. Performance optimization

---

This documentation provides a comprehensive guide to the Aksio backend infrastructure and operations. For specific technical details, refer to the individual documentation files linked above.