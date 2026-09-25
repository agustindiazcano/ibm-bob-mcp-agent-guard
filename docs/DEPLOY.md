# Deploying TestMind AI (RepoGuard) to Google Cloud Run

This is the human half of Phase 13 (`PENDING.md`). The Dockerfile and the two
GitHub Actions workflows (`.github/workflows/ci.yml`, `.github/workflows/cd.yml`)
are already in the repo and don't need editing — this document is only the
one-time GCP setup that has to be done by someone with real GCP access,
since no AI agent working on this repo holds cloud credentials.

## 1. One-time GCP setup

```bash
# Pick a project id and region — reuse them exactly in step 3.
export PROJECT_ID=your-project-id
export REGION=us-central1
export REPO_NAME=repoguard
export SERVICE_NAME=repoguard

gcloud config set project "$PROJECT_ID"

# APIs needed
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Artifact Registry repo to hold the container images
gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --description="TestMind AI / repoguard images"

# Service account the GitHub Action will authenticate as
gcloud iam service-accounts create repoguard-deployer \
  --display-name="repoguard CD deployer"

export SA_EMAIL="repoguard-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/run.admin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/iam.serviceAccountUser"

# Key for the GitHub secret (see step 2). Treat this file as a secret —
# delete it locally once it's pasted into GitHub.
gcloud iam service-accounts keys create repoguard-deployer-key.json \
  --iam-account="$SA_EMAIL"
```

A static JSON key is the fastest path for a hackathon deadline. If there's
time afterward, switch to [Workload Identity Federation](https://github.com/google-github-actions/auth#setting-up-workload-identity-federation) instead — no
long-lived key to leak or rotate.

## 2. GitHub repo configuration

Settings → Secrets and variables → Actions.

**Secrets:**
| Name | Value |
|---|---|
| `GCP_SA_KEY` | Contents of `repoguard-deployer-key.json` |

**Variables:**
| Name | Value |
|---|---|
| `GCP_PROJECT_ID` | your project id |
| `GCP_REGION` | e.g. `us-central1` |
| `GAR_REPOSITORY` | e.g. `repoguard` |
| `CLOUD_RUN_SERVICE` | e.g. `repoguard` |

Then delete the local `repoguard-deployer-key.json` — it's only needed to get
its contents into the GitHub secret.

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

## Known limitation

`--allow-unauthenticated` makes the service public. That's the right choice
for a judged demo (nobody clicking a link should hit a login wall), but if
this deployment outlives the hackathon, either add Cloud Run IAM auth or add
your own auth layer in front — `repoguard serve` has none built in.
