export interface ProductDetail {
  rank: number
  product_id: number
  nombre_comercial: string | null
  justification?: string | null
  dosis?: string | null
  precio_estimado?: number | null
  toxicidad?: string | null
  intervalo_seguridad?: number | null
  categoria?: string | null
  cultivo_objetivo?: string | null
  problema_objetivo?: string | null
}

export interface RecommendationData {
  id: number
  ticket_id: string
  crop: string
  crop_stage: string
  problem: string
  status: string
  current_step: string | null
  error_message: string | null
  max_budget_per_liter?: number | null
  budget_range?: string | null
  products: ProductDetail[]
}

export interface ProviderPayload {
  id: string | number
  name?: string
  nombre?: string
  product_name?: string
  producto_asociado?: string
  product_id?: string | number | null
  phone?: string
  telefono?: string
  email?: string
  correo?: string
  location?: string
  ubicacion?: string
  provincia?: string | null
  canton?: string | null
}

export interface NormalizedProvider {
  id: string
  name: string
  productId?: string
  productName: string
  phone: string
  email: string
  location: string
}

export interface ProductComparison {
  rank: number
  productId: string
  name: string
  badge: string
  badgeColor: 'green' | 'blue' | 'amber'
  type: string
  compatibility: string
  price: string
  availability: string
  treatsProblem: string
  budget: string
  risk: string
  application: string
  finalRecommendation: string
}

export interface ComparisonRow {
  label: string
  values: Array<{
    value: string
    tone: 'ok' | 'warning' | 'muted'
  }>
}

const unavailable = 'No disponible'

function normalizeText(value: string | null | undefined) {
  return value?.trim().toLowerCase() ?? ''
}

export function formatColones(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return unavailable
  }

  return `₡ ${new Intl.NumberFormat('es-CR', { maximumFractionDigits: 0 })
    .format(value)
    .replace(/[,.]/g, ' ')
    .replace(/\u00A0/g, ' ')}`
}

export function formatCategory(value: string | null | undefined) {
  if (!value) return unavailable
  return value
    .split('_')
    .join(' ')
    .toLowerCase()
    .replace(/^\w/, (letter) => letter.toUpperCase())
}

export function riskFromToxicity(toxicity: string | null | undefined) {
  const value = normalizeText(toxicity)
  if (!value || value === 'no_aplica') return unavailable
  if (value.includes('verde')) return 'Bajo'
  if (value.includes('azul')) return 'Medio'
  if (value.includes('amarilla')) return 'Alto'
  if (value.includes('roja')) return 'Muy alto'
  return formatCategory(toxicity)
}

export function normalizeProviders(providers: ProviderPayload[]): NormalizedProvider[] {
  return providers.map((provider) => {
    const locationParts = [provider.ubicacion ?? provider.location, provider.provincia, provider.canton]
      .filter(Boolean)
      .map(String)

    return {
      id: String(provider.id),
      name: provider.nombre ?? provider.name ?? unavailable,
      productId: provider.product_id === null || provider.product_id === undefined ? undefined : String(provider.product_id),
      productName: provider.producto_asociado ?? provider.product_name ?? unavailable,
      phone: provider.telefono ?? provider.phone ?? unavailable,
      email: provider.correo ?? provider.email ?? unavailable,
      location: locationParts.length > 0 ? locationParts.join(', ') : unavailable,
    }
  })
}

export function buildProductComparisons(
  recommendation: RecommendationData,
  providers: NormalizedProvider[] = [],
): ProductComparison[] {
  const budget = recommendation.max_budget_per_liter ?? Number(recommendation.budget_range)

  return [...(recommendation.products ?? [])]
    .sort((left, right) => left.rank - right.rank)
    .map((product) => {
      const productProviders = providers.filter((provider) => provider.productId === String(product.product_id))
      const cropTarget = normalizeText(product.cultivo_objetivo)
      const problemTarget = normalizeText(product.problema_objetivo)
      const crop = normalizeText(recommendation.crop)
      const problem = normalizeText(recommendation.problem)
      const price = product.precio_estimado ?? null
      const risk = riskFromToxicity(product.toxicidad)

      return {
        rank: product.rank,
        productId: String(product.product_id),
        name: product.nombre_comercial ?? unavailable,
        badge: product.rank === 1 ? 'Mejor opción' : product.rank === 2 ? 'Alternativa viable' : 'Más económico',
        badgeColor: product.rank === 1 ? 'green' : product.rank === 2 ? 'blue' : 'amber',
        type: formatCategory(product.categoria),
        compatibility: cropTarget ? (cropTarget.includes(crop) || crop.includes(cropTarget) ? 'Excelente' : 'Revisar') : unavailable,
        price: formatColones(price),
        availability:
          productProviders.length > 0
            ? productProviders.length === 1
              ? 'Disponible localmente'
              : `${productProviders.length} proveedores`
            : unavailable,
        treatsProblem: problemTarget ? (problemTarget.includes(problem) || problem.includes(problemTarget) ? 'Sí' : 'Revisar') : unavailable,
        budget:
          price === null || price === undefined || Number.isNaN(price) || Number.isNaN(budget)
            ? unavailable
            : price <= budget
              ? formatColones(price)
              : `${formatColones(price)} fuera de presupuesto`,
        risk,
        application: product.dosis ? 'Fácil' : unavailable,
        finalRecommendation:
          product.rank === 1
            ? 'Altamente recomendado'
            : product.rank === 2
              ? 'Recomendado'
              : risk === 'Bajo'
                ? 'Recomendado'
                : 'Recomendado con reservas',
      }
    })
}

function toneFor(value: string): 'ok' | 'warning' | 'muted' {
  if (value === unavailable) return 'muted'
  if (value.includes('Revisar') || value.includes('reservas') || value.includes('fuera')) return 'warning'
  if (value === 'Alto' || value === 'Muy alto') return 'warning'
  return 'ok'
}

export function buildComparisonRows(products: ProductComparison[]): ComparisonRow[] {
  const rows: Array<[string, keyof ProductComparison]> = [
    ['Compatible con cultivo', 'compatibility'],
    ['Trata el problema', 'treatsProblem'],
    ['Dentro del presupuesto', 'budget'],
    ['Disponible localmente', 'availability'],
    ['Riesgo ambiental', 'risk'],
    ['Facilidad de aplicación', 'application'],
    ['Recomendación final', 'finalRecommendation'],
  ]

  return rows.map(([label, key]) => ({
    label,
    values: products.map((product) => {
      const value = String(product[key] ?? unavailable)
      return { value, tone: toneFor(value) }
    }),
  }))
}
