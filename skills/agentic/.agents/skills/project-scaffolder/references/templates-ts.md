# Project Templates Reference

This document contains ready-to-use project templates with complete directory structures, configuration files, and development scripts.

> **⚠️ Versiones de dependencias**: Las versiones especificadas en este documento fueron verificadas en **2026-05-28**.
> Se recomienda revisar y actualizar las versiones trimestralmente o antes de iniciar un proyecto en producción.
> Usa `pip index versions <package>` (Python) o `npm show <package> version` (Node) para verificar la versión más reciente.

---

## JavaScript / TypeScript Templates

---

### 4. ts-react — React SPA with Vite

**When to use**: Building a single-page application, dashboard, or any client-side rendered frontend. Best for apps that don't need server-side rendering.

#### Directory Tree

```
my-app/
├── public/
│   └── favicon.svg                  # App favicon
├── src/
│   ├── main.tsx                     # React entry point
│   ├── App.tsx                      # Root component with router
│   ├── index.css                    # Global styles, CSS variables
│   ├── vite-env.d.ts                # Vite type declarations
│   ├── components/
│   │   ├── ui/                      # Reusable base components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Card.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Footer.tsx
│   │       └── Sidebar.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── About.tsx
│   │   └── NotFound.tsx
│   ├── hooks/
│   │   ├── useLocalStorage.ts
│   │   └── useMediaQuery.ts
│   ├── services/
│   │   ├── api.ts                   # API client (fetch/axios wrapper)
│   │   └── auth.ts                  # Auth service
│   ├── stores/                      # State management (Zustand)
│   │   └── useAppStore.ts
│   ├── types/
│   │   └── index.ts                 # Shared TypeScript types
│   └── utils/
│       ├── cn.ts                    # Classname utility
│       └── format.ts                # Formatters (date, currency, etc.)
├── tests/
│   ├── setup.ts                     # Vitest setup (jsdom, matchers)
│   ├── components/
│   │   └── Button.test.tsx
│   └── utils/
│       └── format.test.ts
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── eslint.config.js
├── .prettierrc
├── .gitignore
├── .editorconfig
├── .nvmrc
├── index.html
└── README.md
```

#### Core Configuration: `package.json`

```json
{
  "name": "my-app",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.1.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react-swc": "^4.0.0",
    "eslint": "^9.15.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "globals": "^15.12.0",
    "jsdom": "^25.0.0",
    "prettier": "^3.4.0",
    "typescript": "~5.7.0",
    "typescript-eslint": "^8.15.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0",
    "@vitest/coverage-v8": "^2.1.0"
  }
}
```

#### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### `vite.config.ts`

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  server: {
    port: 3000,
    open: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./tests/setup.ts",
    css: true,
  },
});
```

#### `eslint.config.js`

```javascript
import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  }
);
```

#### `.prettierrc`

```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

#### CI Workflow: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "npm"
      - run: npm ci
      - run: npm run type-check
      - run: npm run lint
      - run: npm run format:check
      - run: npm run test -- --run --coverage
      - run: npm run build
```

---

### 5. ts-next — Next.js App Router

**When to use**: Building a full-stack web application, marketing site with SEO, or any project needing server-side rendering, API routes, and React Server Components.

#### Directory Tree

```
my-next-app/
├── app/
│   ├── layout.tsx                   # Root layout (html, body, providers)
│   ├── page.tsx                     # Home page
│   ├── loading.tsx                  # Root loading state
│   ├── error.tsx                    # Root error boundary
│   ├── not-found.tsx                # 404 page
│   ├── globals.css                  # Global styles
│   ├── (marketing)/                 # Route group: marketing pages
│   │   ├── about/
│   │   │   └── page.tsx
│   │   └── pricing/
│   │       └── page.tsx
│   ├── dashboard/                   # Protected dashboard
│   │   ├── layout.tsx               # Dashboard layout (sidebar, nav)
│   │   ├── page.tsx                 # Dashboard home
│   │   └── settings/
│   │       └── page.tsx
│   └── api/
│       └── health/
│           └── route.ts             # Health check API route
├── components/
│   ├── ui/                          # Reusable base components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   └── Input.tsx
│   ├── forms/
│   │   └── ContactForm.tsx
│   └── layout/
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── Sidebar.tsx
├── lib/
│   ├── utils.ts                     # Utility functions
│   ├── constants.ts                 # App constants
│   └── validations.ts              # Zod schemas
├── services/
│   └── api.ts                       # Server-side data fetching
├── types/
│   └── index.ts                     # Shared types
├── public/
│   ├── images/
│   └── fonts/
├── tests/
│   ├── components/
│   │   └── Button.test.tsx
│   └── app/
│       └── page.test.tsx
├── package.json
├── next.config.ts
├── tsconfig.json
├── eslint.config.mjs
├── .prettierrc
├── .env.local.example
├── .gitignore
├── .editorconfig
├── .nvmrc
└── README.md
```

#### Core Configuration: `package.json`

```json
{
  "name": "my-next-app",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "format": "prettier --write \"**/*.{ts,tsx,css,md}\"",
    "format:check": "prettier --check \"**/*.{ts,tsx,css,md}\"",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.1.0",
    "@types/node": "^22.10.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "eslint": "^9.15.0",
    "eslint-config-next": "^15.1.0",
    "jsdom": "^25.0.0",
    "prettier": "^3.4.0",
    "typescript": "~5.7.0",
    "vitest": "^2.1.0",
    "@vitejs/plugin-react-swc": "^4.0.0",
    "@vitest/coverage-v8": "^2.1.0"
  }
}
```

#### `next.config.ts`

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [],
  },
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
```

#### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["DOM", "DOM.Iterable", "ES2023"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "incremental": true,
    "paths": {
      "@/*": ["./*"]
    },
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

#### CI Workflow: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "npm"
      - run: npm ci
      - run: npm run type-check
      - run: npm run lint
      - run: npm run format:check
      - run: npm run test -- --run
      - run: npm run build
        env:
          NEXT_TELEMETRY_DISABLED: 1
```

---

### 6. ts-api — Express/Fastify Backend API

**When to use**: Building a REST API, GraphQL server, or backend service in Node.js. Good for microservices or BFF (Backend for Frontend) patterns.

#### Directory Tree

```
my-server/
├── src/
│   ├── index.ts                     # Server bootstrap
│   ├── app.ts                       # Express/Fastify app setup
│   ├── config/
│   │   ├── env.ts                   # Environment variable validation (zod)
│   │   └── database.ts              # Database connection config
│   ├── routes/
│   │   ├── index.ts                 # Route aggregator
│   │   ├── health.ts                # GET /health
│   │   └── items.ts                 # /api/items CRUD routes
│   ├── controllers/
│   │   └── items.controller.ts      # Request handling logic
│   ├── services/
│   │   └── items.service.ts         # Business logic
│   ├── middleware/
│   │   ├── errorHandler.ts          # Global error handler
│   │   ├── validate.ts              # Zod validation middleware
│   │   └── auth.ts                  # Authentication middleware
│   ├── models/
│   │   └── item.model.ts            # Database model / ORM entity
│   ├── schemas/
│   │   └── item.schema.ts           # Zod schemas for validation
│   ├── types/
│   │   └── index.ts                 # Shared types
│   └── utils/
│       ├── logger.ts                # Pino logger setup
│       └── errors.ts                # Custom error classes
├── tests/
│   ├── setup.ts                     # Test setup
│   ├── helpers/
│   │   └── testApp.ts               # Test app factory
│   ├── integration/
│   │   └── items.test.ts            # API integration tests
│   └── unit/
│       └── items.service.test.ts    # Unit tests
├── package.json
├── tsconfig.json
├── eslint.config.js
├── .prettierrc
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .editorconfig
├── .nvmrc
└── README.md
```

#### Core Configuration: `package.json`

```json
{
  "name": "my-server",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write \"src/**/*.ts\"",
    "format:check": "prettier --check \"src/**/*.ts\"",
    "type-check": "tsc --noEmit",
    "db:migrate": "drizzle-kit migrate",
    "db:generate": "drizzle-kit generate",
    "db:studio": "drizzle-kit studio"
  },
  "dependencies": {
    "express": "^5.0.0",
    "zod": "^3.23.0",
    "pino": "^9.5.0",
    "pino-pretty": "^13.0.0",
    "helmet": "^8.0.0",
    "cors": "^2.8.0",
    "drizzle-orm": "^0.36.0",
    "better-sqlite3": "^11.6.0"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/cors": "^2.8.0",
    "@types/better-sqlite3": "^7.6.0",
    "tsx": "^4.19.0",
    "typescript": "~5.7.0",
    "vitest": "^2.1.0",
    "@vitest/coverage-v8": "^2.1.0",
    "eslint": "^9.15.0",
    "typescript-eslint": "^8.15.0",
    "prettier": "^3.4.0",
    "supertest": "^7.0.0",
    "@types/supertest": "^6.0.0",
    "drizzle-kit": "^0.30.0"
  }
}
```

#### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2023"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

#### `Dockerfile` (Multi-stage)

```dockerfile
# Stage 1: Build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# Stage 2: Production
FROM node:22-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist

EXPOSE 3000
USER node
CMD ["node", "dist/index.js"]
```

#### `docker-compose.yml`

```yaml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./src:/app/src  # Dev hot-reload

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: app_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

#### `eslint.config.js`

```javascript
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.ts"],
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/explicit-function-return-type": "warn",
    },
  }
);
```

#### CI Workflow: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "npm"
      - run: npm ci
      - run: npm run type-check
      - run: npm run lint
      - run: npm run format:check
      - run: npm run test -- --run --coverage
      - run: npm run build

  docker:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t my-server .
      - run: docker run --rm my-server node -e "console.log('Container starts OK')"
```
