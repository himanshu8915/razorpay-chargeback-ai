# Phase 0 Summary: Project Foundation & Setup

## Why did we do Phase 0?
In complex AI systems with multiple moving parts (LangGraph agents, vector databases, standard relational databases, and a frontend), starting directly with feature implementation often leads to messy "spaghetti code." If the database connection logic is tangled with the frontend UI or the agent prompts, the system becomes impossible to test and scale. 

Phase 0 ensures that **before a single line of business logic is written**, the structural foundation is solid. It guarantees that the frontend can talk to the backend, the backend can talk to the database, and the environment is fully reproducible via Docker. This means in Phase 1, we only worry about *data*, not *how to connect to the database*.

## What exactly did we build?

We built the "empty house" where the Chargeback AI will live. This includes:

1. **The Backend Skeleton (FastAPI)**: 
   - A robust Python API application setup.
   - Core foundations like `settings.py` (configuration via environment variables so secrets aren't hardcoded), `exceptions.py` (error handling), and `enums.py` (standardizing terms like `DisputeType` or `CaseStatus`).
   - Placeholder folders for the future LangGraph architecture: `agents/`, `rag/`, `decision/`, etc.
   
2. **The Database Connection (SQLAlchemy)**: 
   - We set up the asynchronous connection pool to PostgreSQL. We didn't create the tables yet, but the "plumbing" is fully connected and ready.

3. **The Frontend Skeleton (Next.js)**: 
   - We initialized a modern React application.
   - We created the API client so the frontend can securely talk to the backend without hardcoding URLs.
   - We built the "Phase 0 Status Dashboard" to visually prove the connection works.

4. **The Infrastructure (Docker)**: 
   - We created `docker-compose.yml` and `Dockerfile`s for the frontend and backend. 
   - We defined the `postgres` database service (using `pgvector` for future AI capabilities).

## How does it work?

When you run `docker compose up --build`:
1. **Docker** creates an isolated network.
2. The **PostgreSQL Database** starts up and exposes port 5432.
3. The **FastAPI Backend** starts up on port 8000. It reads the `.env` file, connects to the database, and exposes the `/api/v1/health` and `/api/v1/ready` endpoints.
4. The **Next.js Frontend** starts up on port 3000. It serves the web UI and routes any requests starting with `/api/v1/*` directly to the backend container.

As a result, when you open the browser at `http://localhost:3000`, the React code asks the backend "Are you ready?", the backend asks the database "Are you there?", and if everything replies "Yes", the dashboard lights up green. 

All of this was accomplished without touching a single business rule or AI prompt, giving us a perfect sandbox for Phase 1.
