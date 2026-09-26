# Codifies the CI/CD identity Phase 13 set up by hand via gcloud (see
# docs/DEPLOY.md §1) — Workload Identity Federation + the deployer service
# account GitHub Actions uses to push images and deploy Cloud Run, with no
# long-lived secret ever stored in GitHub.
#
# These resources already exist for real. This file is meant to be adopted
# with `terraform import` (see infra/terraform/README.md), not applied fresh
# — an apply against empty state would try to re-create resources that are
# already there and fail on the name collision.

locals {
  sa_email = "${var.deployer_service_account_id}@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_service" "required" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_registry_repo
  format        = "DOCKER"
  description   = "TestMind AI / repoguard images"
}

resource "google_service_account" "deployer" {
  project      = var.project_id
  account_id   = var.deployer_service_account_id
  display_name = "repoguard CD deployer"
}

# Additive project-level roles (google_project_iam_member, not the
# authoritative *_iam_binding) — matches how `gcloud projects
# add-iam-policy-binding` created them: alongside whatever else already has
# these roles on the project, never replacing it.
resource "google_project_iam_member" "deployer_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${local.sa_email}"
}

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = var.workload_identity_pool_id
  display_name              = "GitHub Actions pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = var.workload_identity_provider_id
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  # Scoped to this exact repo — no other GitHub repo, even in the same org,
  # can impersonate the deployer service account.
  attribute_condition = "assertion.repository=='${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "workload_identity_user" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}
