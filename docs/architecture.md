# Project Directory Plan

Below is the envisioned high-level structure for the `socials-mcp` open-source server.  Files and folders shown in *italic* are not yet implemented and will be added iteratively.

```text
socials-mcp/                     # <– project root
│
├── .github/                     # CI/CD workflow definitions
│   └── workflows/
│       └── ci.yml               # lint, tests, docker-build, etc.
│
├── .env.example                 # template of environment variables
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
│
├── docker-compose.yml           # local dev stack (db, redis, app, worker)
├── Dockerfile                   # image that runs the API server
│
├── pyproject.toml               # poetry / PEP-621 metadata *or* setup.cfg
├── requirements/                # split requirements if not using poetry
│   ├── base.txt                 # prod deps
│   ├── dev.txt                  # formatter, testing, etc.
│   └── docs.txt
│
├── docs/                        # MkDocs / Sphinx sources, ADRs, diagrams
│   └── architecture.md          # <-- you are here
│
├── scripts/                     # one-off helper scripts (db seed, etc.)
│   └── bootstrap_local.sh
│
└── src/                         # all importable Python packages live here
    └── mcp/                     # top-level application package
        ├── __init__.py
        │
        ├── main.py              # FastAPI application factory
        ├── cli.py               # Typer or Click commands
        │
        ├── api/                 # REST (or GraphQL) routers
        │   ├── __init__.py
        │   ├── v1/              # first public API version
        │   │   ├── __init__.py
        │   │   └── routes/
        │   │       ├── twitter.py
        │   │       ├── youtube.py
        │   │       ├── facebook.py
        │   │       ├── instagram.py
        │   │       └── health.py
        │   └── deps.py          # reusable Depends() providers
        │
        ├── core/                # app-wide concerns
        │   ├── config.py        # pydantic-settings
        │   ├── logging.py *
        │   ├── security.py *    # auth, rate-limiting helpers
        │   └── tasks.py *       # Celery / RQ enqueue helpers
        │
        ├── services/            # business logic (one file per platform)
        │   ├── __init__.py
        │   ├── twitter_service.py *
        │   ├── youtube_service.py *
        │   ├── facebook_service.py *
        │   └── instagram_service.py *
        │
        ├── adapters/            # thin HTTP wrappers around 3-rd-party APIs
        │   ├── __init__.py
        │   ├── youtube_client.py *
        │   ├── twitter_client.py *
        │   └── facebook_client.py *
        │
        ├── models/              # SQLAlchemy / Pydantic models
        │   ├── __init__.py
        │   ├── orm/ *           # DB entities
        │   └── schemas/ *       # request / response DTOs
        │
        ├── repositories/        # persistence abstractions
        │   └── post_repository.py *
        │
        ├── workers/             # background consumers (Celery, Dramatiq…)
        │   └── publish_worker.py *
        │
        ├── utils/               # generic helpers
        │   └── imagekit.py
        │
        └── tests/               # pytest test-suite mirrors src structure
            ├── __init__.py
            ├── unit/
            └── integration/
```

Legend
• Regular text — already present in the repository.
• Asterisk (*) — planned components to be developed.

This document acts as a living blueprint; update it whenever new top-level modules or tooling are introduced. 