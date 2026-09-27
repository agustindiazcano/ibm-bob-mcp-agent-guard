# infra/terraform — CI/CD identity + measurement-history database

Codifies two things, in two files that can be applied independently:

- `cicd.tf` — the Workload Identity Federation setup that `docs/DEPLOY.md` §1
  created by hand via `gcloud` for Phase 13: the `github-pool`/`github-provider`
  WIF pair and the `repoguard-deployer` service account GitHub Actions
  impersonates to push images and deploy Cloud Run. No long-lived GCP secret is
  stored in GitHub either way — Terraform only manages the identity that makes
  that possible, not the day-to-day deploy (that's still `cd.yml`, unchanged).
- `db.tf` — Cloud SQL for PostgreSQL 16 + a Secret Manager secret holding its
  connection string (Phase 17 Block B1, `docs/DATA_PLATFORM.md` §8). This is
  new infrastructure -- unlike `cicd.tf`, it has nothing to `terraform import`;
  it's created fresh by `apply`.

Scope on purpose, for both files: this only provisions what the app actually
uses. Cloud Run itself has never been Terraform-managed here (still deployed
by `cd.yml`'s `gcloud run deploy`) -- wiring the new database onto the live
service is a documented human step below, same as `REPOGUARD_FIX_TOKEN`
already is.

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

## New: provisioning the measurement-history database (`db.tf`)

**Before running this, confirm a GCP billing account is attached to the
project** — Cloud SQL bills for as long as the instance exists, unlike Cloud
Run which scales to zero (`docs/DATA_PLATFORM.md` §8/§13 open question).
`db_tier`'s default (`db-f1-micro`) is the cheapest shared-core tier at the
time this was written; confirm current pricing/availability in the GCP
console before applying, since tier names and availability change.

Unlike `cicd.tf`, nothing here exists yet — no `terraform import` needed:

```bash
cd infra/terraform
terraform init
terraform plan     # review: 1 Cloud SQL instance, 1 database, 1 user,
                    # 1 random password, 1 Secret Manager secret + version,
                    # 2 IAM bindings for the Cloud Run runtime SA
terraform apply    # takes ~10-15 minutes -- Cloud SQL instance creation is slow
terraform output sql_connection_name database_url_secret_id
```

Then, to actually make the live Cloud Run service use it (human step —
Cloud Run isn't Terraform-managed, see above):

```bash
gcloud run services update repoguard --region us-central1 \
  --add-cloudsql-instances=$(terraform output -raw sql_connection_name) \
  --update-secrets=REPOGUARD_DATABASE_URL=$(terraform output -raw database_url_secret_id):latest
```

After that, every `repoguard analyze`/`gate` run against the live service
(and `POST /api/runs` ingests) will persist to this database, and the
`GET /api/projects*` routes (Phase 17 A3/C1) will start returning real data
instead of 503/404.

**When done with a demo and want to stop paying for it:**
`terraform destroy -target=google_sql_database_instance.history` removes the
instance (and, since `deletion_protection = false`, succeeds without a
manual unlock step first) — do this before the DB, not the whole stack, if
`cicd.tf`'s CI/CD identity should stay intact.

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
