# Aksio Backend - Simple Cloud Run Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "api.aksio.app"
}

# Locals
locals {
  name_prefix = "aksio-${var.environment}"
  labels = {
    project     = "aksio"
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Configure provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "storage-api.googleapis.com"
  ])
  
  service = each.value
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "aksio_registry" {
  location      = var.region
  repository_id = "${local.name_prefix}-registry"
  description   = "Aksio application container registry"
  format        = "DOCKER"
  
  labels = local.labels
  
  depends_on = [google_project_service.required_apis]
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "aksio_db" {
  name             = "${local.name_prefix}-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  deletion_protection = var.environment == "prod"
  
  settings {
    tier              = var.environment == "prod" ? "db-n1-standard-1" : "db-f1-micro"
    availability_type = "ZONAL"  # Cheaper than REGIONAL
    disk_size         = var.environment == "prod" ? 50 : 20
    disk_type         = "PD_SSD"
    disk_autoresize   = true
    
    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = var.environment == "prod"
      backup_retention_settings {
        retained_backups = 7
      }
    }
    
    ip_configuration {
      ipv4_enabled    = true
      authorized_networks {
        value = "0.0.0.0/0"  # Allow Cloud Run access
        name  = "all"
      }
    }
    
    user_labels = local.labels
  }
  
  depends_on = [google_project_service.required_apis]
}

# Database
resource "google_sql_database" "aksio_database" {
  name     = "aksio"
  instance = google_sql_database_instance.aksio_db.name
}

# Database user
resource "google_sql_user" "aksio_user" {
  name     = "aksio"
  instance = google_sql_database_instance.aksio_db.name
  password = random_password.db_password.result
}

# Secret Manager secrets
resource "google_secret_manager_secret" "django_secret" {
  secret_id = "${local.name_prefix}-django-secret"
  
  replication {
    automatic = true
  }
  
  labels = local.labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "django_secret_version" {
  secret      = google_secret_manager_secret.django_secret.id
  secret_data = random_password.django_secret.result
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${local.name_prefix}-db-password"
  
  replication {
    automatic = true
  }
  
  labels = local.labels
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "${local.name_prefix}-openai-key"
  
  replication {
    automatic = true
  }
  
  labels = local.labels
}

# Random passwords
resource "random_password" "django_secret" {
  length  = 50
  special = true
}

resource "random_password" "db_password" {
  length  = 16
  special = false
}

# Cloud Storage bucket for static files and media
resource "google_storage_bucket" "aksio_static" {
  name          = "${local.name_prefix}-static-${random_id.bucket_suffix.hex}"
  location      = var.region
  force_destroy = var.environment != "prod"
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  labels = local.labels
  
  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "aksio_media" {
  name          = "${local.name_prefix}-media-${random_id.bucket_suffix.hex}"
  location      = var.region
  force_destroy = var.environment != "prod"
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  labels = local.labels
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${local.name_prefix}-run-sa"
  display_name = "Aksio Cloud Run Service Account"
  description  = "Service account for Aksio Cloud Run service"
}

# IAM bindings for service account
resource "google_project_iam_member" "cloud_run_sa_bindings" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run Service
resource "google_cloud_run_service" "aksio_backend" {
  name     = "${local.name_prefix}-backend"
  location = var.region
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"        = "10"
        "autoscaling.knative.dev/minScale"        = "0"
        "run.googleapis.com/cloudsql-instances"   = google_sql_database_instance.aksio_db.connection_name
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }
    
    spec {
      service_account_name = google_service_account.cloud_run_sa.email
      
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}/aksio-backend:latest"
        
        ports {
          container_port = 8000
        }
        
        env {
          name  = "DJANGO_SETTINGS_MODULE"
          value = "aksio.settings.production"
        }
        
        env {
          name  = "DJANGO_DEBUG"
          value = "False"
        }
        
        env {
          name  = "DJANGO_ALLOWED_HOSTS"
          value = var.domain_name
        }
        
        env {
          name = "DJANGO_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.django_secret.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_password.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openai_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.aksio_static.name
        }
        
        env {
          name  = "GCS_MEDIA_BUCKET_NAME"
          value = google_storage_bucket.aksio_media.name
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_project_service.required_apis]
}

# Allow unauthenticated access to Cloud Run service
resource "google_cloud_run_service_iam_binding" "public_access" {
  location = google_cloud_run_service.aksio_backend.location
  service  = google_cloud_run_service.aksio_backend.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}

# Outputs
output "cloud_run_url" {
  value = google_cloud_run_service.aksio_backend.status[0].url
}

output "database_connection_name" {
  value = google_sql_database_instance.aksio_db.connection_name
}

output "database_url" {
  value     = "postgresql://aksio:${random_password.db_password.result}@/${google_sql_database.aksio_database.name}?host=/cloudsql/${google_sql_database_instance.aksio_db.connection_name}"
  sensitive = true
}

output "static_bucket_name" {
  value = google_storage_bucket.aksio_static.name
}

output "media_bucket_name" {
  value = google_storage_bucket.aksio_media.name
}

output "registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}"
}