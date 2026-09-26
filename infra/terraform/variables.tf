variable "project_id" {
  description = "GCP project hosting the repoguard CI/CD identity and Artifact Registry repo."
  type        = string
  default     = "project-e0ad10c9-0b2f-4dc0-ac6"
}

variable "project_number" {
  description = "Numeric project ID — the WIF principalSet member is expressed with this, not the project_id string."
  type        = string
  default     = "993240087609"
}

variable "region" {
  description = "Region for Artifact Registry and Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "github_repo" {
  description = "owner/repo allowed to impersonate the deployer service account via WIF's attribute-condition."
  type        = string
  default     = "agustindiazcano/ibm-bob-mcp-agent-guard"
}

variable "artifact_registry_repo" {
  description = "Docker Artifact Registry repository name (matches GAR_REPOSITORY in the CD workflow)."
  type        = string
  default     = "repoguard"
}

variable "deployer_service_account_id" {
  description = "Account ID (local part) of the CD deployer service account."
  type        = string
  default     = "repoguard-deployer"
}

variable "workload_identity_pool_id" {
  type    = string
  default = "github-pool"
}

variable "workload_identity_provider_id" {
  type    = string
  default = "github-provider"
}
