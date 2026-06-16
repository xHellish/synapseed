import axios from 'axios'

function formatDetail(detail: unknown): string | null {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) return String(item.msg)
        return null
      })
      .filter(Boolean)
      .join(' ')
  }
  if (typeof detail === 'object' && 'message' in detail) {
    return String(detail.message)
  }
  return null
}

export function getApiErrorMessage(
  error: unknown,
  fallback: string,
  networkFallback = 'No se pudo conectar con el backend. Verifique que el servicio esté corriendo en localhost:8000.',
) {
  if (!axios.isAxiosError(error)) return fallback
  if (!error.response) return networkFallback

  return formatDetail(error.response.data?.detail) ?? fallback
}
