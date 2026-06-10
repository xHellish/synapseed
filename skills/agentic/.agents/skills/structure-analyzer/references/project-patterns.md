# Project Structure Patterns Reference

A practical reference of common project structure patterns organized by technology. Use this document to identify which pattern a project follows and to recommend improvements.

---

## Python Patterns

### Flat Package

Single package with modules at the top level. Simplest structure.

```
my-project/
├── my_package/
│   ├── __init__.py
│   ├── core.py
│   ├── utils.py
│   └── cli.py
├── tests/
│   ├── test_core.py
│   └── test_utils.py
├── setup.py / pyproject.toml
├── requirements.txt
└── README.md
```

**When to use:**
- Small projects or utilities (< 5 modules)
- Single-developer projects
- Simple CLI tools or small libraries

**Pros:**
- Minimal boilerplate
- Easy to understand at a glance
- Quick to set up

**Cons:**
- Doesn't scale well beyond ~10 modules
- No clear separation of concerns
- Hard to organize as complexity grows

**Migration path:** → src layout when the package exceeds ~10 modules or gains multiple contributors.

---

### src Layout (Recommended)

Uses a `src/` directory to isolate the package from project-level files. Prevents accidental imports from the working directory.

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   └── processor.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   └── data.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── product.py
│       └── utils/
│           ├── __init__.py
│           ├── helpers.py
│           └── validators.py
├── tests/
│   ├── unit/
│   │   ├── test_engine.py
│   │   └── test_auth.py
│   └── integration/
│       └── test_api.py
├── docs/
├── pyproject.toml
├── README.md
└── .github/
    └── workflows/
```

**When to use:**
- Medium to large projects
- Libraries published to PyPI
- Projects with multiple contributors
- Any project that needs clean packaging

**Pros:**
- Clean separation between source and project config
- Prevents accidental local imports during development
- Standard recommended by Python Packaging Authority (PyPA)
- Scales well

**Cons:**
- Slightly more setup required
- Deeper nesting for imports

**Migration path:** Already the recommended standard; consider Django/FastAPI patterns for web applications.

---

### Django Project

Apps-based structure with each app encapsulating a domain area.

```
my_project/
├── manage.py
├── my_project/              # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tests/
│   │   │   ├── test_models.py
│   │   │   └── test_views.py
│   │   └── migrations/
│   └── products/
│       ├── ... (same structure)
├── templates/
├── static/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── docker-compose.yml
```

**When to use:**
- Web applications requiring admin interface
- Projects with clear domain boundaries
- Teams familiar with Django ecosystem
- Content-heavy applications

**Pros:**
- Each app is self-contained and reusable
- Built-in admin, ORM, migrations
- Strong convention over configuration
- Excellent for rapid development

**Cons:**
- Heavy framework overhead for simple APIs
- Can become monolithic if apps aren't well-bounded
- Settings management can be complex

**Migration path:** Consider splitting into microservices if individual apps grow too large, or use Django REST Framework for API-heavy projects.

---

### FastAPI Project

Router-based structure organized around API domains.

```
my-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── config.py            # Settings (pydantic-settings)
│   ├── dependencies.py      # Shared dependencies
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── products.py
│   │   └── auth.py
│   ├── models/              # SQLAlchemy/Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── product_service.py
│   ├── repositories/        # Data access layer
│   │   ├── __init__.py
│   │   └── base.py
│   └── middleware/
│       ├── __init__.py
│       └── auth.py
├── tests/
├── alembic/                 # Database migrations
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

**When to use:**
- Modern async REST/GraphQL APIs
- Microservices
- Projects needing auto-generated OpenAPI docs
- Performance-critical APIs

**Pros:**
- Clean separation of routers, services, and data access
- Easy to test each layer independently
- Async-first design
- Automatic API documentation

**Cons:**
- More manual setup than Django
- No built-in admin interface
- Need to choose ORM separately

**Migration path:** Start with flat routers, then extract services and repositories as business logic grows.

---

### Flask Project

Blueprint-based structure for modular Flask applications.

```
my-app/
├── app/
│   ├── __init__.py          # App factory
│   ├── extensions.py        # Flask extensions init
│   ├── blueprints/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   └── main/
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── templates/
│   ├── models/
│   ├── services/
│   ├── static/
│   └── templates/
│       └── base.html
├── tests/
├── config.py
├── wsgi.py
└── requirements.txt
```

**When to use:**
- Small to medium web applications
- Projects needing maximum flexibility
- Teams wanting minimal framework overhead
- Prototypes and MVPs

**Pros:**
- Lightweight and flexible
- Blueprints provide modularity
- Easy to understand
- Large extension ecosystem

**Cons:**
- More decisions to make (ORM, auth, etc.)
- Can become messy without discipline
- No built-in async support (pre-2.0)

**Migration path:** Start with a single module, then add blueprints as the app grows. Consider FastAPI for async-heavy workloads.

---

### Data Science Project (Cookiecutter)

Standard structure for reproducible data science projects.

```
my-ds-project/
├── data/
│   ├── raw/                 # Immutable original data
│   ├── interim/             # Intermediate transformed data
│   ├── processed/           # Final datasets for modeling
│   └── external/            # Third-party data
├── notebooks/               # Jupyter notebooks (numbered)
│   ├── 01_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   └── 03_modeling.ipynb
├── src/
│   ├── __init__.py
│   ├── data/                # Data loading & processing
│   │   ├── make_dataset.py
│   │   └── preprocessing.py
│   ├── features/            # Feature engineering
│   │   └── build_features.py
│   ├── models/              # Model training & prediction
│   │   ├── train.py
│   │   └── predict.py
│   └── visualization/       # Plotting utilities
│       └── visualize.py
├── models/                  # Trained model artifacts
├── reports/
│   └── figures/
├── pyproject.toml
├── Makefile
├── dvc.yaml                 # Data version control
└── README.md
```

**When to use:**
- Machine learning projects
- Research and experimentation
- Projects with data pipelines
- Collaborative data science teams

**Pros:**
- Reproducible workflow
- Clear separation of data, code, and outputs
- Standard across the data science community
- Supports DVC for data versioning

**Cons:**
- Overhead for simple analyses
- Notebooks can create merge conflicts
- Data directories can grow very large

**Migration path:** Start with notebooks, then extract reusable code into `src/` modules. Add DVC when data grows beyond git capacity.

---

## JavaScript/TypeScript Patterns

### Feature-Based (Colocation)

Groups all related files together by feature. Each feature directory is self-contained.

```
my-app/
├── src/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── LoginForm.test.tsx
│   │   │   │   └── LoginForm.module.css
│   │   │   ├── hooks/
│   │   │   │   └── useAuth.ts
│   │   │   ├── services/
│   │   │   │   └── authService.ts
│   │   │   ├── types.ts
│   │   │   └── index.ts
│   │   ├── dashboard/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── types.ts
│   │   │   └── index.ts
│   │   └── settings/
│   │       └── ... (same structure)
│   ├── shared/              # Cross-feature shared code
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── types/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**When to use:**
- Medium to large applications (10+ features)
- Teams of 3+ developers
- Projects with clear domain boundaries
- When features are relatively independent

**Pros:**
- High cohesion within features
- Easy to find all related code
- Features can be developed independently
- Easy to extract into packages or micro-frontends

**Cons:**
- Shared code decisions can be tricky
- Deeper directory nesting
- May have some code duplication across features

**Migration path:** Natural evolution from type-based. Extract features one at a time by moving related files together.

---

### Type-Based (Layered)

Groups files by their type or role. Traditional approach for smaller projects.

```
my-app/
├── src/
│   ├── components/
│   │   ├── ui/              # Generic UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Modal.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   └── forms/
│   │       ├── LoginForm.tsx
│   │       └── RegisterForm.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useLocalStorage.ts
│   │   └── useFetch.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   └── userService.ts
│   ├── stores/ or context/
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   ├── types/
│   │   ├── user.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── styles/
│   │   ├── globals.css
│   │   └── variables.css
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
└── tsconfig.json
```

**When to use:**
- Small to medium projects (< 10 major features)
- Small teams (1-3 developers)
- Projects in early stages
- Simple CRUD applications

**Pros:**
- Simple and intuitive
- Easy to get started
- Low overhead
- Clear where to put new files of a given type

**Cons:**
- Related files are scattered across directories
- Hard to understand feature boundaries
- Doesn't scale well
- Difficult to refactor or extract features

**Migration path:** → Feature-based when the components/ or services/ directories exceed ~20 files.

---

### Next.js App Router

File-system based routing using the `app/` directory. Each route is a directory with special files.

```
my-next-app/
├── app/
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page (/)
│   ├── loading.tsx          # Loading UI
│   ├── error.tsx            # Error boundary
│   ├── not-found.tsx        # 404 page
│   ├── globals.css
│   ├── (auth)/              # Route group (no URL segment)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── dashboard/
│   │   ├── layout.tsx       # Dashboard layout
│   │   ├── page.tsx         # /dashboard
│   │   └── settings/
│   │       └── page.tsx     # /dashboard/settings
│   └── api/
│       └── users/
│           └── route.ts     # API route handler
├── components/              # Shared components
│   ├── ui/
│   └── layout/
├── lib/                     # Utility functions & configs
│   ├── db.ts
│   ├── auth.ts
│   └── utils.ts
├── public/
├── next.config.js
├── package.json
└── tsconfig.json
```

**When to use:**
- Full-stack React applications
- Projects needing SSR/SSG/ISR
- SEO-critical applications
- When you want file-system routing

**Pros:**
- File-system routing reduces boilerplate
- Built-in SSR, SSG, and API routes
- Layouts and loading states are first-class
- Route groups for clean URL structure

**Cons:**
- Framework-specific conventions to learn
- Can be opinionated about project structure
- Server/client component boundary adds complexity

**Migration path:** Start with pages in `app/`, extract shared components to `components/`, and business logic to `lib/`. Use route groups to organize related routes.

---

### Monorepo

Workspace-based structure for managing multiple packages or applications in a single repository.

```
my-monorepo/
├── apps/
│   ├── web/                 # Main web application
│   │   ├── src/
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── mobile/              # Mobile application
│   │   ├── src/
│   │   └── package.json
│   └── docs/                # Documentation site
│       ├── src/
│       └── package.json
├── packages/
│   ├── ui/                  # Shared UI component library
│   │   ├── src/
│   │   │   ├── Button.tsx
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── utils/               # Shared utilities
│   │   ├── src/
│   │   └── package.json
│   ├── config-eslint/       # Shared ESLint config
│   │   └── package.json
│   └── config-typescript/   # Shared TS config
│       ├── base.json
│       └── package.json
├── package.json             # Root workspace config
├── turbo.json               # Turborepo config (if using)
├── pnpm-workspace.yaml      # pnpm workspaces (if using)
└── .github/
    └── workflows/
```

**When to use:**
- Multiple related applications sharing code
- Organizations with shared component libraries
- Projects with separate frontend/backend packages
- Teams building design systems

**Pros:**
- Code sharing without publishing packages
- Consistent tooling and configuration
- Atomic commits across packages
- Single CI/CD pipeline

**Cons:**
- Higher tooling complexity (Turborepo, Nx, Lerna)
- Longer CI times without proper caching
- Dependency version conflicts
- Steeper learning curve

**Migration path:** Start by identifying shared code, then create a workspace config. Move shared code into `packages/` one module at a time. Use Turborepo or Nx for build orchestration.

---

### Library

Structure optimized for publishing a reusable library or package.

```
my-library/
├── src/
│   ├── index.ts             # Main entry point (barrel)
│   ├── core/
│   │   ├── parser.ts
│   │   └── transformer.ts
│   ├── utils/
│   │   ├── helpers.ts
│   │   └── validators.ts
│   └── types/
│       └── index.ts         # Public type definitions
├── tests/
│   ├── parser.test.ts
│   └── transformer.test.ts
├── examples/                # Usage examples
│   ├── basic.ts
│   └── advanced.ts
├── docs/                    # API documentation
├── dist/                    # Build output (gitignored)
├── package.json
├── tsconfig.json
├── tsconfig.build.json      # Build-specific TS config
├── vitest.config.ts
├── .npmignore
├── CHANGELOG.md
├── LICENSE
└── README.md
```

**When to use:**
- npm/PyPI packages
- Internal shared libraries
- Open-source projects
- Utility collections

**Pros:**
- Clear public API via barrel exports
- Easy to version and publish
- Separation of source, tests, and docs
- Examples help users understand usage

**Cons:**
- Overhead for internal-only code
- Barrel files can cause tree-shaking issues if not configured
- Need to maintain build configuration

**Migration path:** Start with a simple `src/index.ts` exporting everything, then organize into subdirectories as the API surface grows. Add examples and docs before publishing.

---

## Pattern Selection Guide

| Factor | Flat / Type-Based | Feature-Based | Monorepo |
|--------|-------------------|---------------|----------|
| Project size | Small | Medium-Large | Multiple projects |
| Team size | 1-3 | 3-10 | 5+ |
| Complexity | Low | Medium-High | High |
| Code sharing needs | None | Within project | Across projects |
| Setup effort | Minimal | Moderate | Significant |
| Scalability | Limited | Good | Excellent |

## Anti-Patterns to Watch For

1. **God Module**: One file doing everything — split into focused modules
2. **Circular Dependencies**: A imports B, B imports A — introduce an interface or shared module
3. **Deeply Nested Directories**: More than 4 levels deep — flatten or restructure
4. **Inconsistent Naming**: Mixing camelCase, kebab-case, and snake_case — pick one and enforce
5. **Missing Barrel Exports**: Every directory imported by path — add index files for clean APIs
6. **Config Sprawl**: Configuration files scattered everywhere — centralize in root or config/
7. **Test Orphans**: Tests that don't correspond to any source file — clean up or restructure
8. **Utility Dumping Ground**: A `utils/` folder with 50+ unrelated functions — split by domain
