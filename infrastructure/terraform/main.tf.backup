# Aksio Backend - Complete GCP Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
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

# Configure providers
provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_client_config" "default" {}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
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

# GKE Cluster
resource "google_container_cluster" "aksio_cluster" {
  name     = "${local.name_prefix}-cluster"
  location = var.region
  
  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1
  
  # Network configuration
  network    = google_compute_network.aksio_vpc.name
  subnetwork = google_compute_subnetwork.aksio_subnet.name
  
  # Cluster configuration
  deletion_protection = false
  
  # Enable services
  monitoring_service = "monitoring.googleapis.com/kubernetes"
  logging_service    = "logging.googleapis.com/kubernetes"
  
  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Enable Network Policy
  network_policy {
    enabled = true
  }
  
  # Enable IP Alias
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "10.1.0.0/16"
    services_ipv4_cidr_block = "10.2.0.0/16"
  }
  
  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Node Pool for applications
resource "google_container_node_pool" "aksio_nodes" {
  name       = "${local.name_prefix}-nodes"
  location   = var.region
  cluster    = google_container_cluster.aksio_cluster.name
  node_count = 2
  
  # Autoscaling
  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }
  
  # Node configuration
  node_config {
    preemptible  = var.environment != "prod"
    machine_type = var.environment == "prod" ? "e2-standard-2" : "e2-medium"
    disk_size_gb = 50
    disk_type    = "pd-ssd"
    
    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    labels = local.labels
    tags   = ["aksio-nodes"]
  }
  
  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
  
  depends_on = [google_project_service.required_apis]
}

# VPC Network
resource "google_compute_network" "aksio_vpc" {
  name                    = "${local.name_prefix}-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

# Subnet
resource "google_compute_subnetwork" "aksio_subnet" {
  name          = "${local.name_prefix}-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.aksio_vpc.name
  
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }
  
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "aksio_db" {
  name             = "${local.name_prefix}-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  deletion_protection = var.environment == "prod"
  
  settings {
    tier              = var.environment == "prod" ? "db-n1-standard-2" : "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = var.environment == "prod" ? 100 : 20
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
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.aksio_vpc.id
      enable_private_path_for_google_cloud_services = true
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
    
    user_labels = local.labels
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
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

# Redis Instance
resource "google_redis_instance" "aksio_redis" {
  name           = "${local.name_prefix}-redis"
  tier           = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = var.environment == "prod" ? 4 : 1
  region         = var.region
  
  location_id             = var.environment == "prod" ? null : "${var.region}-a"
  alternative_location_id = var.environment == "prod" ? "${var.region}-b" : null
  
  authorized_network = google_compute_network.aksio_vpc.id
  
  redis_version     = "REDIS_7_0"
  display_name      = "Aksio Redis Cache"
  
  labels = local.labels
  
  depends_on = [google_project_service.required_apis]
}

# Private service networking
resource "google_compute_global_address" "private_ip_address" {
  name          = "${local.name_prefix}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.aksio_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.aksio_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
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

# Random passwords
resource "random_password" "django_secret" {
  length  = 50
  special = true
}

resource "random_password" "db_password" {
  length  = 16
  special = false
}

# Cloud Storage bucket for static files
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

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Service Account for Workload Identity
resource "google_service_account" "aksio_sa" {
  account_id   = "${local.name_prefix}-sa"
  display_name = "Aksio Application Service Account"
  description  = "Service account for Aksio application pods"
}

# IAM bindings for service account
resource "google_project_iam_member" "aksio_sa_bindings" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.aksio_sa.email}"
}

# Kubernetes Service Account
resource "google_service_account_iam_binding" "workload_identity" {
  service_account_id = google_service_account.aksio_sa.name
  role               = "roles/iam.workloadIdentityUser"
  
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[aksio/aksio-backend]"
  ]
}

# Configure Kubernetes provider
provider "kubernetes" {
  host                   = "https://${google_container_cluster.aksio_cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.aksio_cluster.master_auth.0.cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.aksio_cluster.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.aksio_cluster.master_auth.0.cluster_ca_certificate)
  }
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.aksio_cluster.name
}

output "cluster_endpoint" {
  value = google_container_cluster.aksio_cluster.endpoint
}

output "database_connection_name" {
  value = google_sql_database_instance.aksio_db.connection_name
}

output "redis_host" {
  value = google_redis_instance.aksio_redis.host
}

output "bucket_name" {
  value = google_storage_bucket.aksio_static.name
}

output "registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aksio_registry.repository_id}"
}