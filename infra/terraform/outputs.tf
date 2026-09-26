output "wif_provider" {
  description = "Value for the GitHub repo's WIF_PROVIDER variable (docs/DEPLOY.md §2)."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "deployer_service_account" {
  description = "Value for the GitHub repo's DEPLOYER_SA variable (docs/DEPLOY.md §2)."
  value       = google_service_account.deployer.email
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.images.id
}
