import { apiRequest } from '../../services/api/client'

export const CATEGORIAS_MATERIAL = [
  { value: 'apontamentos', label: 'Apontamentos' },
  { value: 'apresentacao', label: 'Apresentações' },
  { value: 'exercicios', label: 'Exercícios' },
  { value: 'exame', label: 'Exames' },
  { value: 'solucoes', label: 'Soluções' },
  { value: 'outro', label: 'Outro' },
] as const

export type CategoriaMaterial = (typeof CATEGORIAS_MATERIAL)[number]['value']

export type Material = {
  id: string
  titulo: string
  descricao: string | null
  categoria: CategoriaMaterial
  ano_letivo: string | null
  publicado_em: string
  versao_atual: {
    ficheiro: {
      nome_original: string
    }
  }
}

export type PesquisaMateriais = {
  q?: string
  categoria?: CategoriaMaterial
}

export function pesquisarMateriais(criteria: PesquisaMateriais): Promise<Material[]> {
  const params = new URLSearchParams()
  if (criteria.q) params.set('q', criteria.q)
  if (criteria.categoria) params.set('categoria', criteria.categoria)
  const query = params.toString()
  return apiRequest<Material[]>(`/materiais${query ? `?${query}` : ''}`)
}
