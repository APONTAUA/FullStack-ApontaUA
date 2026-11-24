
import { apiRequest } from '../../services/api/client'

export type CategoriaMaterial =
  | 'apontamentos'
  | 'apresentacao'
  | 'exercicios'
  | 'exame'
  | 'solucoes'
  | 'outro'

export type Material = {
  id: string
  titulo: string
  descricao: string | null
  categoria: CategoriaMaterial
  origem: 'comunidade' | 'elearning'
  ano_letivo: string | null
  estado: 'publicado' | 'removido'
  uc_id: string
  topico_id: string
  autor_id: string | null
  publicado_em: string
  versao_atual: {
    numero: number
    criada_em: string
    ficheiro: {
      nome_original: string
      tipo: string
      tamanho_bytes: number
      sha256: string
    }
  }
}

/**
 * Lista os materiais publicados associados a um tópico (US-021).
 */
export type MaterialUpdate = {
  titulo?: string
  descricao?: string | null
  categoria?: CategoriaMaterial
  uc_id?: string
  topico_id?: string
  ano_letivo?: string | null
}

export function updateMaterial(materialId: string, input: MaterialUpdate): Promise<Material> {
  return apiRequest<Material>(`/materiais/${encodeURIComponent(materialId)}`, {
    method: 'PATCH',
    body: input,
  })
}

export function listMateriaisPorTopico(topicoId: string): Promise<Material[]> {
  return apiRequest<Material[]>(
    `/materiais?topico_id=${encodeURIComponent(topicoId)}`,
  )
}
