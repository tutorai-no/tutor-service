# Workload Identity Federation Setup for GitHub Actions

This guide explains how to set up Workload Identity Federation (WIF) to allow GitHub Actions to authenticate with Google Cloud without storing service account keys.

## Prerequisites

- Google Cloud Project: `production-466308`
- `gcloud` CLI installed and authenticated
- Project Owner or IAM Admin permissions

## Step 1: Enable Required APIs

```bash
# Enable only the APIs needed for GitHub Actions deployment
gcloud services enable iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  --project=production-466308
```

Note: We're not enabling Cloud Build API since building happens in GitHub Actions.

## Step 2: Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create "github-pool" \
  --project="production-466308" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

## Step 3: Create Workload Identity Provider

Replace `YOUR_GITHUB_ORG` with your GitHub organization name:

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="production-466308" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'YOUR_GITHUB_ORG'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

## Step 4: Create Service Accounts

### 4.1 Create CI/CD Service Account
```bash
gcloud iam service-accounts create github-actions-ci-cd \
  --project="production-466308" \
  --display-name="GitHub Actions CI/CD"
```

### 4.2 Create Cloud Run Service Account
```bash
gcloud iam service-accounts create aksio-backend-runtime \
  --project="production-466308" \
  --display-name="Aksio Backend Runtime"
```

## Step 5: Grant Permissions

### 5.1 CI/CD Service Account Permissions
```bash
# Artifact Registry permissions
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:github-actions-ci-cd@production-466308.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Run deployment permissions
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:github-actions-ci-cd@production-466308.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# Service Account usage permission
gcloud iam service-accounts add-iam-policy-binding \
  aksio-backend-runtime@production-466308.iam.gserviceaccount.com \
  --member="serviceAccount:github-actions-ci-cd@production-466308.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Cloud SQL client permission (for migrations)
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:github-actions-ci-cd@production-466308.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 5.2 Runtime Service Account Permissions
```bash
# Cloud SQL client
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:aksio-backend-runtime@production-466308.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Cloud Storage permissions
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:aksio-backend-runtime@production-466308.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Secret Manager access (if using)
gcloud projects add-iam-policy-binding production-466308 \
  --member="serviceAccount:aksio-backend-runtime@production-466308.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 6: Configure Workload Identity Binding

Replace `YOUR_GITHUB_ORG` and `YOUR_REPO_NAME` with your actual values:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-ci-cd@production-466308.iam.gserviceaccount.com \
  --project="production-466308" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO_NAME"
```

To get your project number:
```bash
gcloud projects describe production-466308 --format="value(projectNumber)"
```

## Step 7: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create aksio \
  --repository-format=docker \
  --location=europe-west1 \
  --description="Aksio Backend Docker Images" \
  --project=production-466308
```

## Step 8: Get Provider and Service Account Details

Get the Workload Identity Provider resource name:
```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --project="production-466308" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

## Step 9: Configure GitHub Secrets

Add these secrets to your GitHub repository:

1. **WIF_PROVIDER**: The provider resource name from Step 8
   Example: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

2. **WIF_SERVICE_ACCOUNT**: `github-actions-ci-cd@production-466308.iam.gserviceaccount.com`

3. **CLOUD_RUN_SERVICE_ACCOUNT**: `aksio-backend-runtime@production-466308.iam.gserviceaccount.com`

4. **CLOUD_SQL_CONNECTION_NAME**: Your Cloud SQL instance connection name
   Format: `PROJECT_ID:REGION:INSTANCE_NAME`
   Example: `production-466308:europe-west1:aksio-db`

5. **Database and Application Secrets**:
   - DATABASE_NAME
   - DATABASE_USER
   - DATABASE_PASSWORD
   - DJANGO_SECRET_KEY
   - DJANGO_ALLOWED_HOSTS (e.g., `aksio-backend-xxxxx-ew.a.run.app,*.aksio.app`)
   - GCS_BUCKET_NAME
   - GCS_BUCKET_NAME_TEST (for CI tests)
   - OPENAI_API_KEY
   - LLM_PROVIDER (e.g., `openai`)
   - LLM_MODEL (e.g., `gpt-4`)
   - EMAIL_HOST_USER
   - EMAIL_HOST_PASSWORD
   - DEFAULT_FROM_EMAIL
   - REDIS_URL (if using Memorystore)
   - SCRAPER_SERVICE_URL
   - RETRIEVER_SERVICE_URL
   - STRIPE_SECRET_KEY
   - STRIPE_PUBLIC_KEY
   - STRIPE_WEBHOOK_SECRET
   - SENTRY_DSN (optional)

## Step 10: Test the Setup

1. Push to a feature branch to test the CI workflow
2. Merge to main to test the CD workflow
3. Check Cloud Run logs for any issues

## Troubleshooting

### Authentication Issues
If you see authentication errors, verify:
1. The attribute condition in the provider matches your GitHub org
2. The repository path in the workload identity binding is correct
3. All required APIs are enabled

### Permission Issues
Check the service account permissions:
```bash
gcloud projects get-iam-policy production-466308 \
  --flatten="bindings[].members" \
  --format='table(bindings.role)' \
  --filter="bindings.members:github-actions-ci-cd@production-466308.iam.gserviceaccount.com"
```

### Cloud SQL Connection Issues
Ensure the Cloud SQL instance has:
1. Private IP enabled (recommended) or public IP with Cloud SQL Proxy
2. The correct connection name in secrets
3. Database and user created

## Security Best Practices

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Attribute Conditions**: Use repository-specific conditions to limit access
3. **Separate Service Accounts**: Use different accounts for CI/CD and runtime
4. **Regular Audits**: Review IAM permissions periodically
5. **No Key Files**: This setup eliminates the need for service account key files

## Costs

Workload Identity Federation itself is free. You only pay for:
- API calls (negligible for CI/CD)
- Google Cloud resources (Cloud Run, Cloud SQL, etc.)
- No additional costs compared to using service account keys