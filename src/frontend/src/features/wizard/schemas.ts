import { z } from 'zod'

export const caseStep1Schema = z.object({
  finca_id: z.string().optional(),
  finca_name: z.string().optional(),
  crop: z.string().min(1, 'Seleccione cultivo'),
  crop_stage: z.string().min(1, 'Seleccione etapa'),
  affected_area: z.number().min(0).max(100).optional(),
  // Opcionales cuando se selecciona una finca (se toman de la zona)
  soil_type: z.string().optional(),
  humidity: z.string().optional(),
  temperature: z.string().optional(),
  water_quality: z.string().optional(),
  problem_to_solve: z.string().min(1, 'Seleccione problema'),
  last_agrochemical: z.string().optional(),
  max_budget_per_liter: z.number().min(0),
})

export type CaseStep1Form = z.infer<typeof caseStep1Schema>
