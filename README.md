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


## Architecture

- See `ARCHITECTURE.md` for a high-level overview and diagram of how the system works.

## Non-technical glossary

- **Next.js**: The framework that powers the website (pages and small server functions). Hosted on Vercel.
- **Vercel**: The hosting platform for the website, optimized for speed and scale.
- **Vertex AI**: Google’s AI service the app uses to draft and improve proposal text.
- **Cloud Run**: Google’s service that runs the Python AI app on demand in the cloud.
- **FastAPI**: The toolkit the Python app uses to expose web endpoints (like “generate a proposal”).
- **Google Docs API**: Lets the app create/export your final draft into a Google Doc.
- **Google Forms API**: Lets the app import answers you collected in a Google Form.
- **GCS (Cloud Storage)**: Where large files are stored in the cloud.
- **Chunked uploads**: A safer way to upload large files piece-by-piece so a hiccup doesn’t restart from zero.



