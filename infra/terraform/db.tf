# Cloud SQL for PostgreSQL 16 + Secret Manager (Phase 17 Block B1,
# docs/DATA_PLATFORM.md §8). Provisions the measurement-history database the
# repoguard_engine/store/ layer already knows how to talk to.
#
# Scope on purpose, same principle as cicd.tf: this only provisions the
# database and the secret holding its connection string. It does NOT touch
# Cloud Run -- Cloud Run itself has never been Terraform-managed here (it's
# deployed by cd.yml's `gcloud run deploy`), so wiring REPOGUARD_DATABASE_URL
# and the Cloud SQL volume onto the live service stays a documented human
# step (see infra/terraform/README.md), same as REPOGUARD_FIX_TOKEN already is.
#
# Cost note: Cloud SQL bills while it exists, unlike Cloud Run which scales
# to zero. `terraform destroy` (or -target this file's resources) when it
# isn't needed, e.g. after a demo -- see docs/DATA_PLATFORM.md §8's decision
# table and its open question on billing-account availability.

resource "google_project_service" "sql_apis" {
  for_each = toset([
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_sql_database_instance" "history" {
  project             = var.project_id
  name                = var.db_instance_name
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = false # demo/hackathon project -- docs/DATA_PLATFORM.md §8 decision table

  settings {
    tier    = var.db_tier
    edition = "ENTERPRISE"

    ip_configuration {
      ipv4_enabled = true
      # No authorized_networks block: reachable only through the Cloud SQL
      # connector's unix socket (IAM-authenticated), never a raw public-IP
      # allowlist -- docs/DATA_PLATFORM.md §8's "DB network path" decision.
    }

    backup_configuration {
      enabled = false # demo data -- not worth paying for backups
    }
  }

  depends_on = [google_project_service.sql_apis]
}

resource "google_sql_database" "app" {
  project  = var.project_id
  name     = var.db_name
  instance = google_sql_database_instance.history.name
}

resource "random_password" "db" {
  length  = 24
  special = false # keeps the connection-string URL free of characters that need percent-encoding
}

resource "google_sql_user" "app" {
  project  = var.project_id
  name     = var.db_user
  instance = google_sql_database_instance.history.name
  password = random_password.db.result
}

locals {
  # docs/DATA_PLATFORM.md §8's exact connection-string shape for the Cloud
  # SQL unix-socket connector -- matches what repoguard_engine/store/db.py's
  # get_engine() expects in REPOGUARD_DATABASE_URL.
  database_url = "postgresql+psycopg://${var.db_user}:${random_password.db.result}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.history.connection_name}"
}

resource "google_secret_manager_secret" "database_url" {
  project   = var.project_id
  secret_id = "repoguard-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.sql_apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = local.database_url
}

# The Cloud Run runtime service account (the default compute SA -- the same
# one already granted roles/aiplatform.user by hand for Vertex, per
# PENDING.md Phase 14 gap 8) needs to reach both Cloud SQL and this secret.
resource "google_project_iam_member" "runtime_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.runtime_service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.runtime_service_account_email}"
}
