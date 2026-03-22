# AffiForge - The Micro-SaaS That Prints Money

**If it doesn't increase user affiliate revenue, it dies.**

## Quickstart
1. `git clone https://github.com/yourname/affiforge.git`
2. `docker compose up --build`
3. Visit http://localhost:3000 -> sign up -> connect WP + Amazon tag
4. Run your first Reddit scan -> watch money flow in.

## Tech Stack
- Backend: FastAPI + Python 3.12 + LangChain + Celery + Redis
- Frontend: Next.js 15 + Tailwind + Shadcn + Recharts
- DB: PostgreSQL + SQLAlchemy 2.0
- AI: OpenAI GPT-4o / Claude 3.5 Sonnet (swap easily)
- Integrations: PRAW, Amazon PA-API, Serper.dev, WordPress REST, Stripe, Supabase Auth

## Philosophy
Every line of code must move the revenue needle. No bloat.
