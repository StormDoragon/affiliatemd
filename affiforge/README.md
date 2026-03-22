# AffiForge

AI-assisted affiliate operations stack with a FastAPI backend and Next.js frontend.

## Project Layout

- backend: API, orchestration, services, DB models, workers.
- frontend: Operator dashboard and content workflow UI.
- docs: Architecture, prompts, API, legal/compliance, and roadmap docs.
- infra: Docker and deployment infrastructure definitions.
- scripts: Seed and test-content generators.

## Quickstart

### Backend

1. cd backend
2. python -m venv .venv && source .venv/bin/activate
3. pip install -r requirements.txt
4. uvicorn src.main:app --reload

### Frontend

1. cd frontend
2. npm install
3. npm run dev

## License

MIT
