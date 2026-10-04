# ProofGraph

ProofGraph is an evidence workspace for teams responding to RFPs and questionnaires. This repository contains an early, runnable product foundation: a React/Vite workspace and a Django REST API with organization-scoped records, evidence provenance, questionnaire answers, and review actions.

## Development

Requirements: Python 3.12+, Node.js 20+, PostgreSQL with pgvector, Redis, and Docker Compose (optional). Docker is not installed in every development environment; run the services separately if needed.

1. Copy `.env.example` to `.env` and set `SECRET_KEY`, database, and Redis values.
2. Start infrastructure: `docker compose up -d db redis`.
3. Backend: `cd apps/api; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python manage.py migrate; python manage.py runserver`.
4. Frontend: `cd apps/web; npm.cmd install; npm.cmd run dev`.
5. API schema: `/api/schema/`; interactive docs: `/api/docs/`; health: `/health/`.

The default AI provider is a deterministic development provider that abstains when evidence is insufficient. Set `AI_PROVIDER=openai` and configure credentials to enable model-backed drafting. Never use the development provider as production AI. Uploaded files use local storage by default; production should configure the S3-compatible adapter.

## Security and current scope

Tenant ownership is represented explicitly and endpoints scope lookups to the authenticated user's active organization. The foundation includes password authentication, organizations/memberships, evidence records with source locators, questionnaire questions, draft answers/citations, review tasks, and audit events. Parsing, embeddings, production AI, robust exports, invitation delivery, and billing providers still require completion before a production launch. The product does not claim those integrations work yet. See `docs/architecture/system.md` and `docs/development-status.md`.

Do not deploy with `DEBUG=True`, the development AI provider, or local file storage. Configure TLS, secret management, backups, rate limiting, email verification/reset delivery, and managed infrastructure before serving real customer data.
