# Development status

This repository is an initial working foundation, not a production-ready or complete MVP. The app has an organization-scoped API, JWT authentication and registration endpoints, document/version upload, queued format parsers, source-located unverified evidence, evidence verification, questionnaire/question/answer models, deterministic evidence-grounded abstaining drafts, citation-required approval, audit and approval events, and a live React workspace.

The following requested capabilities remain unfinished and must not be represented as working: organization/user administration and invitations; email verification and password reset delivery; questionnaire upload and question extraction; AI vendor adapters and embeddings; semantic/hybrid retrieval; claim normalization and conflict/freshness workflows; commitments analysis; team routing and review assignment UI; XLSX/DOCX/CSV/PDF export; notifications; S3 storage; billing; API rate limits; detailed retention/soft deletion; production observability; and end-to-end workflow coverage.

The mock provider is deterministic and abstains without verified evidence; it is intended only for development. Uploaded files are stored locally by default. Docker is required to run the compose stack and is not available in all environments.
