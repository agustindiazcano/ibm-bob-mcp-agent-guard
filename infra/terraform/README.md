# infra/terraform — CI/CD identity

Codifies the Workload Identity Federation setup that `docs/DEPLOY.md` §1
created by hand via `gcloud` for Phase 13: the `github-pool`/`github-provider`
WIF pair and the `repoguard-deployer` service account GitHub Actions
impersonates to push images and deploy Cloud Run. No long-lived GCP secret is
stored in GitHub either way — Terraform only manages the identity that makes
that possible, not the day-to-day deploy (that's still `cd.yml`, unchanged).

Scope on purpose: this only covers what already exists for real (Phase 13).
Cloud SQL, Secret Manager and the rest of Phase 17 Block B1's original list
stay out until Phase 17 Block A (the database store itself) is actually
built — Terraform shouldn't create infrastructure nothing in the app uses yet.

## One-time: adopt the existing resources

These resources were created manually and already exist. Running `terraform
apply` against empty state would try to create them again and fail on the
name collision — import them into state first, once:

```bash
cd infra/terraform
terraform init

terraform import google_artifact_registry_repository.images \
  projects/project-e0ad10c9-0b2f-4dc0-ac6/locations/us-central1/repositories/repoguard

terraform import google_service_account.deployer \
  projects/project-e0ad10c9-0b2f-4dc0-ac6/serviceAccounts/repoguard-deployer@project-e0ad10c9-0b2f-4dc0-ac6.iam.gserviceaccount.com

for ROLE in roles/artifactregistry.writer roles/run.admin roles/iam.serviceAccountUser; do
  terraform import "google_project_iam_member.deployer_roles[\"$ROLE\"]" \
    "project-e0ad10c9-0b2f-4dc0-ac6 $ROLE serviceAccount:repoguard-deployer@project-e0ad10c9-0b2f-4dc0-ac6.iam.gserviceaccount.com"
done

terraform import google_iam_workload_identity_pool.github \
  projects/project-e0ad10c9-0b2f-4dc0-ac6/locations/global/workloadIdentityPools/github-pool

terraform import google_iam_workload_identity_pool_provider.github \
  projects/project-e0ad10c9-0b2f-4dc0-ac6/locations/global/workloadIdentityPools/github-pool/providers/github-provider

terraform import google_service_account_iam_member.workload_identity_user \
  "projects/project-e0ad10c9-0b2f-4dc0-ac6/serviceAccounts/repoguard-deployer@project-e0ad10c9-0b2f-4dc0-ac6.iam.gserviceaccount.com roles/iam.workloadIdentityUser principalSet://iam.googleapis.com/projects/993240087609/locations/global/workloadIdentityPools/github-pool/attribute.repository/agustindiazcano/ibm-bob-mcp-agent-guard"

for API in run.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com sts.googleapis.com; do
  terraform import "google_project_service.required[\"$API\"]" "project-e0ad10c9-0b2f-4dc0-ac6/$API"
done

terraform plan   # expect "No changes" once every import above succeeds
```

`terraform import` only reads the resource and records it in local state —
it never creates, modifies or deletes anything in GCP. `terraform plan`
after importing everything is the actual proof the code matches reality; if
it shows changes, the `.tf` here has drifted from what `gcloud` actually set
up and needs fixing before ever running `apply`.

## After that

State is local (`terraform.tfstate`, gitignored — never commit it, it can
contain sensitive attribute values). For a project this size that's an
accepted tradeoff, not a recommendation to scale it up as-is; if this ever
grows a real team or a second environment, move to a remote backend (GCS)
before anyone else runs `apply`.

Day-to-day CD (`cd.yml`) never touches Terraform — it authenticates with the
already-existing WIF provider and short-lived tokens, same as before this
directory existed. Terraform only matters again if the identity itself needs
to change (new repo, rotated service account, additional roles).

## Known gap vs. tighter setups

The three project-level roles (`artifactregistry.writer`, `run.admin`,
`iam.serviceAccountUser`) are broader than strictly needed — they're
project-wide because that's how the original `gcloud` setup in
`docs/DEPLOY.md` granted them, and this file codifies what's real rather
than silently tightening live IAM as a side effect of adding Terraform.
Scoping down to this one Artifact Registry repo and this one Cloud Run
service (mirroring `google_artifact_registry_repository_iam_member` /
`google_cloud_run_v2_service_iam_member` instead of project roles) is a
reasonable follow-up, but it's a real permissions change against a live
project and deserves its own deliberate PR, not a bundle-in here.
