# Documentation Templates Reference

Plantillas listas para usar para los tipos de documentación más comunes.

---

## README Template

```markdown
<div align="center">

# 🚀 Project Name

**One-line description of what this project does and for whom.**

[![CI](https://github.com/org/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/org/repo/actions)
[![Coverage](https://codecov.io/gh/org/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/org/repo)
[![Version](https://img.shields.io/github/v/release/org/repo)](https://github.com/org/repo/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ✨ Features

- Feature 1 — brief explanation
- Feature 2 — brief explanation
- Feature 3 — brief explanation

## ⚡ Quick Start

```bash
# Install
pip install project-name
# or
npm install project-name

# Run
project-name --help
```

## 📦 Installation

### Prerequisites
- Python 3.12+ / Node 20+
- PostgreSQL 16+ (for database features)

### Steps

```bash
git clone https://github.com/org/repo.git
cd repo
cp .env.example .env   # Configure your env vars
pip install -e ".[dev]"
make dev               # Start development server
```

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `SECRET_KEY` | — | JWT signing key (min 32 chars) |
| `DEBUG` | `false` | Enable debug mode |
| `PORT` | `8000` | Server port |

## 📖 Usage

### Basic Example

```python
from project_name import Client

client = Client(api_key="your-key")
result = client.do_something(param="value")
print(result)
```

### Advanced Example

```python
# More complex usage example
```

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Format
ruff format src/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📚 Documentation

Full documentation at [docs.example.com](https://docs.example.com).

## 🤝 Contributing

PRs are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[MIT](LICENSE) © [Author Name](https://github.com/author)
```

---

## CONTRIBUTING Template

```markdown
# Contributing to Project Name

Thank you for your interest in contributing!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -e ".[dev]"`
4. Copy `.env.example` to `.env` and configure
5. Run tests: `pytest` — all should pass

## Branching Strategy

- `main` — production-ready code, protected
- `develop` — integration branch
- `feature/description` — feature branches
- `fix/description` — bug fix branches

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add coupon code support to orders
fix: prevent negative prices when discount > base_price
docs: add runbook for high-latency incidents
test: add parametrized tests for pricing tiers
chore: update dependencies to latest patch versions
```

## Pull Request Process

1. Create a branch from `develop`
2. Make your changes with tests
3. Ensure `pytest` and `ruff check` pass
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Open a PR against `develop` with a clear description
6. Address review feedback
7. Squash and merge

## Code Standards

- 80%+ test coverage for new code
- Type hints on all public functions
- Docstrings on all public APIs (Google style)
- No breaking changes without a major version bump
```

---

## MkDocs Configuration

```yaml
# mkdocs.yml
site_name: Project Name
site_description: Brief project description
site_url: https://docs.example.com
repo_url: https://github.com/org/repo
repo_name: org/repo

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      toggle:
        icon: material/brightness-7
        name: Dark mode
    - scheme: slate
      primary: indigo
      toggle:
        icon: material/brightness-4
        name: Light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true

nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
  - User Guide:
    - Configuration: guide/configuration.md
    - Usage: guide/usage.md
  - API Reference: api/
  - Contributing: contributing.md
  - Changelog: changelog.md

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - tables
```

---

## TypeDoc Configuration (TypeScript)

```json
{
  "$schema": "https://typedoc.org/schema.json",
  "entryPoints": ["src/index.ts"],
  "out": "docs/api",
  "name": "Project Name API",
  "readme": "README.md",
  "includeVersion": true,
  "categorizeByGroup": true,
  "plugin": ["typedoc-plugin-markdown"],
  "excludePrivate": true,
  "excludeProtected": false,
  "excludeExternals": true
}
```

---

## Onboarding Guide Template

```markdown
# Developer Onboarding Guide

Welcome to the team! This guide gets you from zero to productive in one day.

## Day 1: Environment Setup (2 hours)

### Step 1: Access & Accounts
- [ ] GitHub organization access (ask your manager)
- [ ] AWS/GCP/Azure console access
- [ ] 1Password team vault access
- [ ] PagerDuty account setup
- [ ] Slack: join #engineering, #alerts, #deployments

### Step 2: Local Setup
- [ ] Clone all repos listed in [repos.md](repos.md)
- [ ] Follow each repo's README setup instructions
- [ ] Run the full test suite — all should pass
- [ ] Start the local development environment

### Step 3: First PR
- [ ] Fix a `good-first-issue` ticket
- [ ] Follow the contributing guide
- [ ] Get your first PR reviewed and merged

## Architecture Overview

[Link to architecture diagram]

We use a [modular monolith / microservices / etc.] architecture. The key services are:

| Service | Responsibility | Repo | Owner |
|---------|---------------|------|-------|
| Orders API | Order management | [link] | @backend-team |
| Inventory | Stock management | [link] | @platform-team |
| Notifications | Email/SMS/Push | [link] | @backend-team |

## Key Resources

- [ADRs](./adrs/) — Architecture decisions
- [Runbooks](./runbooks/) — Incident response guides
- [API Docs](https://api.docs.example.com) — OpenAPI reference
- [Dashboard](https://grafana.example.com) — System health
```
