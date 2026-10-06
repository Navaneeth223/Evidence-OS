# ProofGraph

ProofGraph is an evidence workspace for teams responding to RFPs and questionnaires. This repository contains an early, runnable product foundation: a React/Vite workspace and a Django REST API with organization-scoped records, evidence provenance, questionnaire answers, and review actions.

## Development

Requirements: Python 3.12+, Node.js 20+, PostgreSQL with pgvector, Redis, and Docker Compose (optional). Docker is not installed in every development environment; run the services separately if needed.

1. Copy `.env.example` to `.env` and set `SECRET_KEY`, database, and Redis values.
2. Start infrastructure: `docker compose up -d db redis`.
3. Backend: `cd apps/api; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python manage.py migrate; python manage.py runserver`.
4. Worker: in another terminal, activate the same Python environment and run `cd apps/api; celery -A config worker --loglevel=INFO`.
5. Frontend: `cd apps/web; npm install; npm run dev`.
6. Open `http://localhost:5173` and create a workspace from the sign-in dialog.
7. API schema: `/api/schema/`; interactive docs: `/api/docs/`; health: `/health/`.

The default AI provider is a deterministic development provider that abstains when evidence is insufficient. Set `AI_PROVIDER=openai`, `AI_API_KEY`, and `AI_MODEL` to enable the OpenAI Responses adapter; use `AI_API_BASE_URL` for a compatible endpoint. The configured provider receives the buyer question and selected verified evidence excerpts. PostgreSQL document processing also creates fixed-size mock hash vectors by default; they are for deterministic development only. Set `EMBEDDING_PROVIDER=openai`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL=text-embedding-3-small`, and `EMBEDDING_DIMENSIONS=1536` to generate model embeddings. This sends evidence text and search questions to the configured embedding endpoint. SQLite skips vector storage and uses keyword search. Never use the development providers as production AI. Uploaded files use local storage by default; production should configure the S3-compatible adapter.

To run the complete local stack with containers, create `.env` first, then run `docker compose up --build`. The web UI can register a user and organization; there is no seeded demo account.

## Security and current scope

Tenant ownership is represented explicitly and endpoints scope lookups to the authenticated user's active organization. The foundation includes password authentication, organizations/memberships, async source parsing, heuristic questionnaire import, source-located evidence, cited answer drafts, review and approval records, and normalized XLSX export. Embeddings, Anthropic support, semantic retrieval, robust commitment validation, invitation delivery, and billing providers still require completion before a production launch. See `docs/architecture/system.md` and `docs/development-status.md`.

Do not deploy with `DEBUG=True`, the development AI provider, or local file storage. Configure TLS, secret management, backups, rate limiting, email verification/reset delivery, and managed infrastructure before serving real customer data.
