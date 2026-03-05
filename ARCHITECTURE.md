# Architecture Decision Record — job-hunter

> This document captures the technology choices made for the `job-hunter` project,
> including what each technology is, why it was chosen, and its trade-offs.

---

## Project Vision

A web app for developers searching for their next job. Users upload their CV (PDF),
the app extracts and structures their professional profile, and displays it in a
clean, editable interface.

**Future capabilities** (deferred — not MVP):
- LLM-powered gap analysis: paste a job description → get a study/practice roadmap
- GitHub integration: connect repos to enrich the developer profile
- LinkedIn job posting scraper (legal risk — requires careful evaluation)

---

## MVP Scope

1. **PDF Upload** — user uploads their CV as a PDF file
2. **Profile Extraction** — parse the PDF and extract structured data (experience, education, skills)
3. **Profile Visualization** — a page to view and manually edit the extracted profile

Everything else is deferred to later phases.

---

## Technology Stack

### 1. Next.js (Frontend + API Layer)

**What it is:**
Next.js is a React-based framework for building full-stack web applications. It handles
both the user interface (React components) and server-side logic (API routes) in a single
project, with built-in support for routing, server-side rendering, and static generation.

**Why we chose it:**
- Single language (TypeScript) across UI and API reduces context switching
- API routes eliminate the need for a separate Node/Express server for non-AI endpoints
- File-based routing makes the project structure self-documenting
- Large ecosystem, great DX, easy deployment (Vercel or Docker)
- Strong TypeScript support out of the box

**Pros:**
- Full-stack in one framework — less boilerplate
- React for UI gives access to a massive component ecosystem
- Built-in image optimization, routing, and middleware
- Can be deployed as a static site or a server-rendered app

**Cons:**
- Can become a "monolith" if not structured carefully
- Server Components / App Router mental model has a learning curve
- Not ideal for heavy CPU-bound tasks (that's what the Python service handles)

---

### 2. FastAPI (AI/LLM Microservice)

**What it is:**
FastAPI is a modern Python web framework for building APIs. It is built on top of
Starlette and Pydantic, offering automatic OpenAPI documentation, type validation,
and async support out of the box.

**Why we chose it:**
- Python is the dominant language for AI/ML tooling — using FastAPI keeps us in that ecosystem
- The PDF parsing and (future) LLM work lives here, isolated from the TypeScript layer
- Automatic request/response validation via Pydantic reduces boilerplate
- Async support means it handles concurrent requests efficiently

**Pros:**
- Fastest Python web framework for APIs (comparable to Node.js)
- Auto-generated `/docs` (Swagger UI) for free
- Type safety via Pydantic models
- Easy to extend with LangChain, OpenAI SDK, etc. later

**Cons:**
- Adds a second language/runtime (Python) to the project
- Requires Docker or a Python environment to run locally
- Inter-service communication (Next.js ↔ FastAPI) adds a network hop

---

### 3. LangChain *(Deferred — Phase 2)*

**What it is:**
LangChain is a Python (and JS) framework for building applications powered by Large
Language Models. It provides abstractions for prompt management, chaining LLM calls,
memory, and tool use (e.g., web search, code execution).

**Why it's planned:**
- Will power the profile-vs-job-description gap analysis feature
- Provides model-agnostic abstractions (swap OpenAI for Anthropic, local models, etc.)
- Handles prompt templates, output parsers, and retrieval pipelines cleanly

**Deferred because:**
- Not needed until the LLM feature is in scope
- Profile model must be stable before gap analysis can be designed
- Adds API cost complexity (needs budgeting + caching strategy)

---

### 4. PDFMiner / PyMuPDF (PDF Parsing)

**What it is:**
PDFMiner and PyMuPDF (also known as `fitz`) are Python libraries for extracting text,
images, and layout data from PDF files.

- **PDFMiner**: Pure Python, excellent for text extraction with layout awareness
- **PyMuPDF**: C-based binding, faster and more robust for complex PDFs

**Why we chose it:**
- CV parsing is a core MVP requirement
- Both libraries are battle-tested for text extraction
- Python-native — fits naturally in the FastAPI service

**Pros:**
- PDFMiner: great layout/position metadata (useful for structured extraction)
- PyMuPDF: faster, handles more PDF variants, supports images

**Cons:**
- PDF parsing is inherently noisy — real-world CVs have inconsistent formatting
- Neither library "understands" a CV structure — that logic must be built on top
- Multi-column layouts, tables, and graphics can confuse parsers

**Decision**: Start with PyMuPDF for speed and robustness; fall back to PDFMiner if
layout metadata is needed for smarter extraction.

---

### 5. PostgreSQL + pgvector (Database)

**What it is:**
PostgreSQL is a powerful, open-source relational database. `pgvector` is a PostgreSQL
extension that adds a vector data type and similarity search operations — enabling
semantic/embedding-based search directly in Postgres.

**Why we chose it:**
- PostgreSQL is a proven, production-grade relational DB for storing structured profile data
- `pgvector` future-proofs the DB for the LLM feature: embeddings for profile/JD matching
  can live in the same database without introducing a separate vector store (e.g., Pinecone)
- Single DB for both relational and vector data reduces operational complexity

**Why Docker for the DB:**
- Avoids "works on my machine" problems — everyone on the team gets the same Postgres version
- No local installation required — just `docker compose up`
- Easy to reset, seed, and version the database configuration
- Matches how it would run in production (containerized)

**Pros:**
- Relational + vector in one place
- Docker makes setup reproducible across machines
- pgvector is well-supported and production-ready
- No additional managed service needed for MVP

**Cons:**
- pgvector is not as performant as dedicated vector DBs (Pinecone, Weaviate) at massive scale
- Docker adds a layer of complexity for developers unfamiliar with containers
- Schema migrations require tooling (we'll add one in a later phase)

---

### 6. Turborepo (Monorepo Build Orchestration)

**What it is:**
Turborepo is a high-performance build system for JavaScript/TypeScript monorepos. It
caches build outputs and runs tasks (build, test, lint) in parallel across packages,
only rebuilding what changed.

**Why we chose it:**
- The project is a monorepo (Next.js frontend + shared types + potentially other JS packages)
- Turborepo's caching dramatically speeds up CI and local development
- Works seamlessly with pnpm workspaces (see below)

**Pros:**
- Remote caching: share build cache across the team and CI
- Parallel task execution out of the box
- Zero-config for common setups
- First-class TypeScript support

**Cons:**
- Adds a build layer on top of the monorepo — more config files
- Overkill for very small projects (acceptable trade-off for future growth)
- The Python service is outside the JS build graph and must be managed separately

---

### 7. pnpm Workspaces (Package Manager + Monorepo Foundation)

**What it is:**
pnpm is a fast, disk-efficient Node.js package manager. "Workspaces" is a feature that
allows multiple packages (e.g., `apps/web`, `packages/shared-types`) to live in a single
repository and share dependencies, with pnpm managing them from a single `node_modules`
store using hard links.

**Why we chose it over npm/yarn:**
- Significantly faster installs than npm/yarn
- Strict dependency isolation by default (prevents phantom dependency bugs)
- Native workspace support — no extra tooling needed for cross-package imports
- Works as the foundation that Turborepo sits on top of

**Pros:**
- 2-3x faster installs vs npm
- Disk space savings via content-addressable store (hard links, not copies)
- Strict mode prevents accidental use of undeclared dependencies
- `workspace:*` protocol for cross-package references

**Cons:**
- Slightly different mental model than npm/yarn (can trip up new contributors)
- Some older tools have pnpm compatibility issues (rare, but possible)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                            │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP
┌───────────────────▼─────────────────────────────────────┐
│              Next.js App (TypeScript)                   │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │  React UI   │  │  API Routes (/api/*)              │  │
│  │  (pages)    │  │  - POST /api/cv/upload            │  │
│  └─────────────┘  │  - GET  /api/profile/:id          │  │
│                   └──────────────┬───────────────────┘  │
└──────────────────────────────────┼──────────────────────┘
                                   │ HTTP (internal)
┌──────────────────────────────────▼──────────────────────┐
│           FastAPI Service (Python)                      │
│  - PDF parsing (PyMuPDF)                                │
│  - Profile extraction logic                             │
│  - [Future] LangChain / LLM gap analysis                │
└──────────────────────────────────┬──────────────────────┘
                                   │ SQL + pgvector
┌──────────────────────────────────▼──────────────────────┐
│        PostgreSQL + pgvector (Docker)                   │
│  - profiles table                                       │
│  - [Future] embeddings column for semantic search       │
└─────────────────────────────────────────────────────────┘
```

---

## Monorepo Structure (planned)

```
job-hunter/
├── apps/
│   └── web/               # Next.js app
├── services/
│   └── ai/                # FastAPI Python service
├── packages/
│   └── shared-types/      # TypeScript types shared across apps
├── docker-compose.yml     # PostgreSQL + pgvector
├── turbo.json             # Turborepo config
├── pnpm-workspace.yaml    # pnpm workspaces config
├── ARCHITECTURE.md        # This file
└── README.md
```

---

## Deferred Features (Backlog)

| Feature | Reason Deferred | Notes |
|---|---|---|
| LLM gap analysis | Profile model must stabilize first | Will use LangChain + OpenAI/Anthropic |
| GitHub integration | Phase 2 — adds complexity to auth | OAuth + repo reading permissions needed |
| LinkedIn scraper | Legal risk (ToS violation) | Evaluate alternatives (job board APIs) |

---

*Last updated: 2026-03-05*
