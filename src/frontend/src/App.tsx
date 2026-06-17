// Componente placeholder. La app real se enruta desde `@/app/router` (ver main.tsx).
// Se mantiene porque algunos tests montan <App /> directamente.

export function App() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gradient-to-b from-primary-50 to-white p-8 text-center">
      <div className="flex flex-col items-center gap-2">
        <span className="text-6xl">🌱</span>
        <h1 className="text-4xl font-bold text-primary-700">SynapSeed</h1>
        <p className="max-w-md text-balance text-muted-foreground">
          Plataforma de recomendación de agroquímicos para agricultores
          costarricenses.
        </p>
      </div>

      <div className="rounded-lg border border-primary-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-lg font-semibold text-primary-800">
          ✅ Fase 0 — Setup completado
        </h2>
        <p className="text-sm text-muted-foreground">
          El frontend, backend, base de datos, worker y Redis están listos.
          Las pantallas reales se implementan a partir de la fase 5.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs">
          <span className="rounded-full bg-primary-100 px-3 py-1 text-primary-700">
            React 19
          </span>
          <span className="rounded-full bg-primary-100 px-3 py-1 text-primary-700">
            Vite 6
          </span>
          <span className="rounded-full bg-primary-100 px-3 py-1 text-primary-700">
            Tailwind v4
          </span>
          <span className="rounded-full bg-primary-100 px-3 py-1 text-primary-700">
            TypeScript 5.7
          </span>
        </div>
      </div>

      <a
        href="http://localhost:8000/docs"
        target="_blank"
        rel="noreferrer"
        className="text-sm text-primary-600 underline-offset-4 hover:underline"
      >
        Ver documentación de la API →
      </a>
    </div>
  )
}

export default App
