# Deploying TestMind AI (RepoGuard) to Google Cloud Run

This is the human half of Phase 13 (`PENDING.md`). The Dockerfile and the two
GitHub Actions workflows (`.github/workflows/ci.yml`, `.github/workflows/cd.yml`)
are already in the repo and don't need editing — this document is only the
one-time GCP setup that has to be done by someone with real GCP access,
since no AI agent working on this repo holds cloud credentials.

## 1. One-time GCP setup — done for this project

Auth uses **Workload Identity Federation** (WIF), not a static JSON key —
GitHub Actions exchanges its own OIDC token for short-lived Google
credentials at run time, so no long-lived secret is ever stored in GitHub.
This was set up for real, reusing the same GCP project already configured
for Vertex AI (`docs/VERTEX_SETUP.md`).

**Now managed as code**: `infra/terraform/` (Phase 17 Block B1) codifies
this identity — see `infra/terraform/README.md` for the one-time
`terraform import` that adopted these already-existing resources, confirmed
with a real `terraform plan` showing "No changes" against the live project.
Changing the identity going forward (new repo, rotated SA, additional
roles) should go through Terraform, not another one-off `gcloud` call. The
commands below are kept as the historical record of what was actually run
to create these resources the first time:

```bash
PROJECT_ID=project-e0ad10c9-0b2f-4dc0-ac6
PROJECT_NUMBER=993240087609
REGION=us-central1
REPO_NAME=repoguard
GITHUB_REPO=agustindiazcano/ibm-bob-mcp-agent-guard

gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com --project="$PROJECT_ID"

gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker --location="$REGION" \
  --description="TestMind AI / repoguard images" --project="$PROJECT_ID"

gcloud iam service-accounts create repoguard-deployer \
  --display-name="repoguard CD deployer" --project="$PROJECT_ID"

SA_EMAIL="repoguard-deployer@${PROJECT_ID}.iam.gserviceaccount.com"
for ROLE in roles/artifactregistry.writer roles/run.admin roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$ROLE" --condition=None
done

gcloud iam workload-identity-pools create github-pool \
  --location=global --display-name="GitHub Actions pool" --project="$PROJECT_ID"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global --workload-identity-pool=github-pool \
  --display-name="GitHub OIDC" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com" --project="$PROJECT_ID"

gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}" \
  --project="$PROJECT_ID"
```

The `--attribute-condition` on the OIDC provider restricts impersonation to
this exact repo — no other GitHub repo can use this service account, even
one in the same org.

## 2. GitHub repo configuration

Settings → Secrets and variables → Actions → **Variables** tab (no Secrets
needed at all — that's the point of WIF):

| Name | Value |
|---|---|
| `GCP_PROJECT_ID` | `project-e0ad10c9-0b2f-4dc0-ac6` |
| `GCP_REGION` | `us-central1` |
| `GAR_REPOSITORY` | `repoguard` |
| `CLOUD_RUN_SERVICE` | `repoguard` |
| `WIF_PROVIDER` | `projects/993240087609/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `DEPLOYER_SA` | `repoguard-deployer@project-e0ad10c9-0b2f-4dc0-ac6.iam.gserviceaccount.com` |

## 3. First deploy

Push to `main`, or run the `CD — Deploy to Cloud Run` workflow manually
(Actions tab → select it → "Run workflow"). The job builds the image from
the repo's `Dockerfile`, pushes it to Artifact Registry, and deploys it to
Cloud Run with `--allow-unauthenticated` (public URL, no auth — fine for a
hackathon demo; tighten this afterward if the service stays up).

The live URL is in the `deploy-cloudrun` step's output in the Actions run
log, and in the Cloud Run console under the service name.

## 4. What's demoable out of the box

The image bundles `demo-repo/`, so once deployed:
- `https://<service-url>/` — the dashboard
- `https://<service-url>/api/analyze?repo_path=demo-repo` — real measured JSON
- The "Stream" button in the dashboard hits `/api/stream?repo_path=demo-repo` for the live SSE progress view

Visual checks (screenshots, accessibility) will report a per-call error in
this image — Playwright's Chromium browser binary isn't installed to keep
the image small. See the comment in `Dockerfile` for the one line that adds
it back if a visual-regression demo is needed.

## 5. Enabling Autofix (`POST /api/fix`) — human step

Autofix runs the AI fix loop over HTTP, so it spends Vertex AI quota for
several minutes per run. It's off (`503`) until the service has a
`REPOGUARD_FIX_TOKEN`; the dashboard sends it as `Authorization: Bearer
<token>` from a password field that's never stored. One run at a time
per instance (`409` otherwise; add `--max-instances=1` if you need a hard
global limit); each run works on a temporary copy of the repo and never
commits or opens a PR (`repoguard_engine/web/fix_job.py`).

Store the token in Secret Manager, let the Cloud Run runtime service
account read it, and attach it to the service. This is the same kind of
IAM grant as `roles/aiplatform.user` in Session 21, which an agent session
can't make:

```bash
PROJECT=project-e0ad10c9-0b2f-4dc0-ac6
RUNTIME_SA=993240087609-compute@developer.gserviceaccount.com

gcloud services enable secretmanager.googleapis.com --project "$PROJECT"
openssl rand -hex 24 | gcloud secrets create repoguard-fix-token \
  --project "$PROJECT" --replication-policy=automatic --data-file=-
gcloud secrets add-iam-policy-binding repoguard-fix-token --project "$PROJECT" \
  --member="serviceAccount:$RUNTIME_SA" --role=roles/secretmanager.secretAccessor
gcloud run services update repoguard --project "$PROJECT" --region us-central1 \
  --update-secrets=REPOGUARD_FIX_TOKEN=repoguard-fix-token:latest

# The token to paste into the dashboard:
gcloud secrets versions access latest --secret=repoguard-fix-token --project "$PROJECT"
```

Later `cd.yml` deploys keep the secret reference, because
`deploy-cloudrun` only changes what it's given. `cd.yml` already sets
`--timeout=1800` so a full run isn't cut off at Cloud Run's default 300 s.

## Known limitation

`--allow-unauthenticated` makes the service public. That's the right choice
for a judged demo (nobody clicking a link should hit a login wall), but if
this deployment outlives the hackathon, either add Cloud Run IAM auth or add
your own auth layer in front — `repoguard serve` has none built in, except
for `POST /api/fix`, which is token-gated (section 5).
