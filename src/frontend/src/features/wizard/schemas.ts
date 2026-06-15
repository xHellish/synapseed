import { z } from 'zod'

export const caseStep1Schema = z.object({
  finca_id: z.string().min(1, 'Seleccione una finca'),
  finca_name: z.string().optional(),
  crop: z.string().min(1, 'Seleccione cultivo'),
  crop_stage: z.string().min(1, 'Seleccione etapa'),
  affected_area: z.number().min(0).max(100).optional(),
  soil_type: z.string().min(1, 'Seleccione tipo de suelo'),
  humidity: z.string().min(1, 'Seleccione humedad'),
  temperature: z.string().min(1, 'Seleccione temperatura'),
  water_quality: z.string().min(1, 'Seleccione calidad del agua'),
  problem_to_solve: z.string().min(1, 'Seleccione problema'),
  last_agrochemical: z.string().optional(),
  max_budget_per_liter: z.number().min(0),
})

export type CaseStep1Form = z.infer<typeof caseStep1Schema>
