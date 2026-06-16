import { describe, expect, it } from 'vitest'

import {
  buildComparisonRows,
  buildProductComparisons,
  formatColones,
  normalizeProviders,
  riskFromToxicity,
  type RecommendationData,
} from './recommendationMapper'

const recommendation: RecommendationData = {
  id: 1,
  ticket_id: 'ticket',
  crop: 'Tomate',
  crop_stage: 'Floración',
  problem: 'Hongo en las hojas',
  status: 'completed',
  current_step: null,
  error_message: null,
  max_budget_per_liter: 10000,
  products: [
    {
      rank: 1,
      product_id: 10,
      nombre_comercial: 'FungiShield Pro',
      dosis: 'Aplicación foliar',
      precio_estimado: 9000,
      toxicidad: 'verde',
      intervalo_seguridad: 3,
      categoria: 'Fungicida Sistémico',
      cultivo_objetivo: 'Tomate',
      problema_objetivo: 'Hongo en las hojas',
    },
  ],
}

describe('recommendationMapper', () => {
  it('formats colones with prototype spacing', () => {
    expect(formatColones(10000)).toBe('₡ 10 000')
    expect(formatColones(null)).toBe('No disponible')
  })

  it('normalizes Spanish provider payloads', () => {
    const providers = normalizeProviders([
      {
        id: 5,
        nombre: 'AgroSuministros del Valle',
        product_id: 10,
        producto_asociado: 'FungiShield Pro',
        telefono: '2345 - 6789',
        correo: 'ventas@agrovalle.cr',
        ubicacion: 'Cartago, Pacayas',
      },
    ])

    expect(providers[0]).toMatchObject({
      id: '5',
      name: 'AgroSuministros del Valle',
      productId: '10',
      productName: 'FungiShield Pro',
      email: 'ventas@agrovalle.cr',
    })
  })

  it('derives comparison values from recommendation facts', () => {
    const products = buildProductComparisons(
      recommendation,
      normalizeProviders([{ id: 1, nombre: 'Proveedor', product_id: 10 }]),
    )
    const rows = buildComparisonRows(products)

    expect(products[0]).toMatchObject({
      compatibility: 'Excelente',
      price: '₡ 9 000',
      treatsProblem: 'Sí',
      risk: 'Bajo',
      finalRecommendation: 'Altamente recomendado',
    })
    expect(rows.find((row) => row.label === 'Disponible localmente')?.values[0]).toMatchObject({
      value: 'Disponible localmente',
      tone: 'ok',
    })
  })

  it('maps toxicity risk without inventing missing values', () => {
    expect(riskFromToxicity('roja')).toBe('Muy alto')
    expect(riskFromToxicity(undefined)).toBe('No disponible')
  })
})
