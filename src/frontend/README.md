# SynapSeed — Frontend

SPA construida con **React 19 + Vite 6 + TypeScript 5.7 + TailwindCSS v4**.

## Stack

- **React 19** + **Vite 6** (build tool con HMR instantáneo)
- **TypeScript 5.7** con strict mode
- **TailwindCSS v4** (CSS-first config, sin `tailwind.config.js`)
- **shadcn/ui** (componentes copiados al repo, ver `components.json`)
- **TanStack Query 5** (cache de servidor, refetch automático)
- **Zustand 5** (estado de cliente: auth tokens, wizard, theme)
- **React Router 7** (rutas declarativas)
- **React Hook Form + Zod** (formularios con validación)
- **Axios** (cliente HTTP con interceptores JWT)
- **Vitest** + **React Testing Library** + **Playwright** (tests)
- **ESLint 9** (flat config) + **Prettier**

## Estructura

```
src/frontend/
├── public/                    # assets estáticos (favicon, etc.)
├── src/
│   ├── app/                   # Setup global
│   │   ├── main.tsx           # Entry point
│   │   ├── App.tsx            # Componente raíz (placeholder fase 0)
│   │   └── router.tsx         # Rutas (fase 0: solo "/")
│   ├── components/            # (fase 5) componentes compartidos
│   │   └── ui/                # (fase 5) shadcn/ui generados
│   ├── features/              # (fase 5) módulos por dominio
│   ├── hooks/                 # (fase 5) hooks globales
│   ├── lib/                   # Utilidades
│   │   └── cn.ts              # clsx + tailwind-merge
│   ├── stores/                # (fase 5) Zustand stores
│   ├── styles/
│   │   └── globals.css        # Tailwind v4 + tokens
│   ├── test/
│   │   └── setup.ts           # Vitest global setup
│   └── types/                 # (fase 5) tipos globales
├── components.json            # shadcn/ui config
├── eslint.config.js
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── .prettierrc.json
├── .env.example
├── package.json
└── Dockerfile
```

## Setup local

```bash
# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.example .env
# (opcional) editar VITE_API_URL si el backend no está en localhost:8000

# Levantar dev server con HMR
npm run dev
# → http://localhost:5173
```

## Scripts

| Script | Descripción |
|---|---|
| `npm run dev` | Dev server con HMR en `http://localhost:5173` |
| `npm run build` | Type-check + build de producción en `dist/` |
| `npm run preview` | Previsualizar el build de producción |
| `npm run lint` | ESLint |
| `npm run lint:fix` | ESLint con autofix |
| `npm run format` | Prettier (auto-formatea) |
| `npm run typecheck` | TypeScript sin emitir archivos |
| `npm run test` | Vitest (correr una vez) |
| `npm run test:watch` | Vitest en watch mode |
| `npm run test:coverage` | Vitest con reporte de cobertura |
| `npm run test:e2e` | Playwright E2E |

## Tokens del sistema de diseño

Definidos en `src/styles/globals.css` con la sintaxis `@theme` de Tailwind v4:

- **Colores primarios:** `primary-50` a `primary-900` (paleta verde agrícola)
- **Colores secundarios:** `secondary-*` (tierra/marrón)
- **Semánticos:** `success`, `warning`, `error`, `info`
- **Neutrales:** `background`, `foreground`, `muted`, `border`, `ring`
- **Tipografía:** `font-sans` (Inter), `font-mono` (JetBrains Mono)
- **Radius:** `radius-sm` a `radius-xl`

## Aliases de imports

Definidos en `tsconfig.app.json` + `vite.config.ts`:

```ts
import { cn } from '@/lib/cn'
import { router } from '@/app/router'
import { useAuth } from '@/stores/authStore' // (fase 5)
```

## Convenciones

- **Componentes:** PascalCase, un componente por archivo
- **Hooks:** camelCase, prefijo `use`
- **Stores:** Zustand, un store por dominio
- **Estilos:** Tailwind utility classes + tokens semánticos
- **Tipos:** TypeScript estricto, sin `any`
- **Tests:** Co-locados (`Component.test.tsx` junto a `Component.tsx`)

## Agregar componentes de shadcn/ui

```bash
# Inicializar (solo una vez)
npx shadcn@latest init

# Agregar componentes específicos
npx shadcn@latest add button card input label select dialog toast badge separator alert
```

Los componentes se copian a `src/components/ui/`.
