import { Link } from 'react-router-dom'

export function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F7F8F2] p-6 text-[#111827]">
      <section className="w-full max-w-xl rounded-3xl border border-[#E5E7EB] bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-semibold text-[#111827]">Crear cuenta</h1>
        <p className="mt-2 text-sm text-[#6B7280]">Esta pantalla puede ampliarse con el formulario de registro del MVP.</p>
        <Link to="/login" className="mt-6 inline-flex text-sm font-semibold text-primary-700 hover:text-primary-800">
          ← Volver a iniciar sesión
        </Link>
      </section>
    </main>
  )
}
