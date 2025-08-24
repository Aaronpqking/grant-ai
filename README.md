# Grant AI (consolidated)

This repository contains the Grant AI system: a Python backend with agent scripts and a Next.js frontend (`grant-proposal-frontend/`).

Quick layout:

- `vertex_grant_agent.py`, `async_artifact_service.py`, `simple_cloud_agent.py` — backend agent and service scripts
- `deploy_cloud.sh`, `deploy-with-large-uploads.sh`, `cloudbuild.yaml`, `Dockerfile` — deployment helpers
- `grant-proposal-frontend/` — Next.js frontend (see that directory's `README.md` and `DEPLOYMENT.md`)

Development

1. Backend (Python)

```bash
# create a venv (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_tests.py
# run an agent or service
python vertex_grant_agent.py
```

2. Frontend (Next.js)

```bash
cd grant-proposal-frontend
npm install
npm run dev
```

Deployment

See `grant-proposal-frontend/DEPLOYMENT.md` for Vercel deployment details. Backend deployment helpers are provided (`Dockerfile`, `cloudbuild.yaml`, `deploy_cloud.sh`).

Notes

- Duplicate files consolidated from the previous working copy. A backup agent was moved to `grant-ai-repo/archive/`.
- Local virtualenvs were removed from the repository trees and added to `.gitignore`.

Google Docs export

This project includes a stub API at `grant-proposal-frontend/src/pages/api/export/google-docs.ts` that demonstrates how to export generated proposals to Google Docs. To enable this in production:

1. Create a Google Cloud service account with Drive and Docs API access.
2. Grant the service account access to a Drive folder or use domain-wide delegation.
3. Install and use `googleapis` to create a document and return the shareable link from the API endpoint.



