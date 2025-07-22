# Simple Continuous Deployment using Cloud Build
# This is the recommended approach for production use

# Enable Cloud Build API if not already enabled
resource "google_project_service" "cloudbuild_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Service account for Cloud Build deployments
resource "google_service_account" "cloud_build_deploy_sa" {
  account_id   = "${local.name_prefix}-build-deploy"
  display_name = "Cloud Build Deploy Service Account"
  description  = "Service account for Cloud Build to deploy to Cloud Run"
}

# Grant necessary permissions to Cloud Build service account
resource "google_project_iam_member" "cloud_build_deploy_permissions" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.reader",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_build_deploy_sa.email}"
}

# Allow Cloud Build to act as the Cloud Run service account
resource "google_service_account_iam_member" "cloud_build_impersonate_run" {
  service_account_id = google_service_account.cloud_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloud_build_deploy_sa.email}"
}

# Grant Cloud Build access to secrets
resource "google_secret_manager_secret_iam_member" "cloud_build_secret_access" {
  for_each = toset([
    google_secret_manager_secret.django_secret.secret_id,
    google_secret_manager_secret.openai_api_key.secret_id
  ])

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_build_deploy_sa.email}"
}

# Cloud Build trigger for automatic deployment
resource "google_cloudbuild_trigger" "auto_deploy" {
  name        = "${local.name_prefix}-auto-deploy"
  description = "Automatically deploy new images to Cloud Run"

  # Trigger when new images are pushed to Artifact Registry
  trigger_template {
    project_id = var.project_id
    repo_name  = "gcr.io/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}"
    tag_name   = ".*"  # Trigger on any tag
  }

  # Use inline build configuration
  build {
    # Step 1: Deploy to Cloud Run
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run",
        "deploy",
        google_cloud_run_service.aksio_backend.name,
        "--image", "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}/aksio-backend:$TAG_NAME",
        "--region", var.region,
        "--platform", "managed",
        "--no-traffic"  # Deploy without routing traffic immediately
      ]
    }

    # Step 2: Run database migrations on the new revision
    step {
      name = "gcr.io/cloud-builders/gcloud"
      entrypoint = "bash"
      args = [
        "-c",
        <<-EOT
        # Get the latest revision
        REVISION=$(gcloud run revisions list \
          --service=${google_cloud_run_service.aksio_backend.name} \
          --region=${var.region} \
          --format="value(name)" \
          --limit=1)
        
        # Run migrations using Cloud Run jobs (one-off execution)
        gcloud run jobs create migrate-$${REVISION} \
          --image=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}/aksio-backend:$TAG_NAME \
          --region=${var.region} \
          --command=python,manage.py,migrate,--noinput \
          --set-env-vars=DJANGO_SETTINGS_MODULE=aksio.settings.production \
          --set-cloudsql-instances=${google_sql_database_instance.aksio_db.connection_name} \
          --service-account=${google_service_account.cloud_run_sa.email} \
          --max-retries=1 \
          --wait
        
        # Execute the migration job
        gcloud run jobs execute migrate-$${REVISION} \
          --region=${var.region} \
          --wait
        
        # Delete the job after completion
        gcloud run jobs delete migrate-$${REVISION} \
          --region=${var.region} \
          --quiet
        EOT
      ]
    }

    # Step 3: Route traffic to the new revision
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run",
        "services",
        "update-traffic",
        google_cloud_run_service.aksio_backend.name,
        "--to-latest",
        "--region", var.region
      ]
    }

    # Build configuration
    options {
      logging               = "CLOUD_LOGGING_ONLY"
      dynamic_substitutions = true
    }

    # Timeout for the entire build
    timeout = "1200s"  # 20 minutes
  }

  # Only trigger on specific tags (optional)
  included_files = ["latest", "v*"]

  service_account = google_service_account.cloud_build_deploy_sa.id

  depends_on = [
    google_project_service.cloudbuild_api,
    google_cloud_run_service.aksio_backend,
    google_project_iam_member.cloud_build_deploy_permissions
  ]
}

# Alternative: Simple trigger without migrations
resource "google_cloudbuild_trigger" "auto_deploy_simple" {
  name        = "${local.name_prefix}-auto-deploy-simple"
  description = "Simple deployment without migrations"
  disabled    = true  # Disabled by default, enable if you prefer this approach

  trigger_template {
    project_id = var.project_id
    repo_name  = "gcr.io/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}"
    tag_name   = "latest"
  }

  build {
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run",
        "deploy",
        google_cloud_run_service.aksio_backend.name,
        "--image", "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}/aksio-backend:latest",
        "--region", var.region,
        "--platform", "managed"
      ]
    }

    options {
      logging = "CLOUD_LOGGING_ONLY"
    }

    timeout = "600s"
  }

  service_account = google_service_account.cloud_build_deploy_sa.id
}

# Output trigger information
output "auto_deploy_trigger_id" {
  value       = google_cloudbuild_trigger.auto_deploy.trigger_id
  description = "ID of the automatic deployment trigger"
}

output "deployment_instructions" {
  value = <<-EOT
  
  Continuous Deployment is now configured!
  
  To trigger a deployment:
  1. Push a new image to Artifact Registry with any tag
  2. The deployment will automatically:
     - Deploy the new image to Cloud Run (without traffic)
     - Run database migrations
     - Route traffic to the new revision
  
  To push an image:
  docker tag your-image ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}/aksio-backend:latest
  docker push ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}/aksio-backend:latest
  
  Monitor deployments:
  gcloud builds list --limit=5
  
  EOT
}