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

output "sql_connection_name" {
  description = "Cloud SQL connection name. Attach to the live service with `gcloud run services update repoguard --add-cloudsql-instances=<this>` (human step, see infra/terraform/README.md)."
  value       = google_sql_database_instance.history.connection_name
}

output "database_url_secret_id" {
  description = "Secret Manager secret id holding REPOGUARD_DATABASE_URL's value. Attach with `gcloud run services update repoguard --update-secrets=REPOGUARD_DATABASE_URL=<this>:latest` (human step)."
  value       = google_secret_manager_secret.database_url.secret_id
}
