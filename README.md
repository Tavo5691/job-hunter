# job-hunter

I want to build an app for developers searching for their next job. The app should allow the user to upload their CV in pdf format, analyze to create a profile of their current experience, It could contain a section for the user to manually enter more information about their experience/education.

Ideal Features (needs analisis):
- Allows to paste a job description and matches the current profile, proposing steps to study/practice for possible upcoming interviews.
- Allows the user to upload their CV in pdf format, analyze to create a profile of their current experience, allow connecting certain github repos to showcase learned languages, patterns, frameworks, methodologies, this will also be used to fill in the profile.
- Some way to connect to Linkedin? Maybe just scraping Linkedin job postings if possible

Things to consider:
- Webapp, desktop app, CLI? Pros/Cons/whats more useful to the target audience?
- Technologies? We should build a monorepo with backend and frontend, but what technologies could be useful?
- Leverage LLMs for certain tasks? This could be a future improvement once the "profile" model is defined and refined
- What's needed to properly match profile vs job descriptions?

Let's think up of an MVP first.

## Development Setup

### Prerequisites
- Node.js >= 20 (via fnm recommended)
- pnpm >= 9
- Python >= 3.11
- uv (Python package manager)
- Docker + Docker Compose

### Quick Start

1. Clone and install JS deps:
   ```bash
   pnpm install
   ```

2. Start the database:
   ```bash
   docker compose up -d
   ```

3. Set up Python environment:
   ```bash
   cd apps/api
   cp .env.example .env
   uv sync
   uv run alembic upgrade head
   ```

4. Set up Next.js:
   ```bash
   cd apps/web
   cp .env.example .env.local
   ```

5. Run everything:
   ```bash
   # Terminal 1 — FastAPI
   cd apps/api && uv run uvicorn app.main:app --reload --port 8000

   # Terminal 2 — Next.js
   pnpm --filter @job-hunter/web dev
   ```

6. Open http://localhost:3000