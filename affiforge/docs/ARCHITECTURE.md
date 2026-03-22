# Architecture

AffiForge uses a modular backend/frontend split:

- FastAPI for API and orchestration.
- Celery for background workflows.
- Next.js App Router for operations UI.
- PostgreSQL (recommended) for persistence.
- Redis for queueing and caching.
