import { apiRequest } from '../../services/api/client'

export type Curso = {
  id: string
  codigo: string
  nome: string
}

export type CursoInput = {
  codigo: string
  nome: string
}

export const CODIGO_MAX_LENGTH = 20
export const NOME_MAX_LENGTH = 200

export function listCursos(): Promise<Curso[]> {
  return apiRequest<Curso[]>('/cursos')
}

export function createCurso(input: CursoInput): Promise<Curso> {
  return apiRequest<Curso>('/cursos', { method: 'POST', body: input })
}

export function updateCurso(id: string, input: Partial<CursoInput>): Promise<Curso> {
  return apiRequest<Curso>(`/cursos/${id}`, { method: 'PATCH', body: input })
}

export function deleteCurso(id: string): Promise<void> {
  return apiRequest<void>(`/cursos/${id}`, { method: 'DELETE' })
}

export type UnidadeCurricular = {
  id: string
  codigo: string
  nome: string
}

export function listUnidadesCurriculares(): Promise<UnidadeCurricular[]> {
  return apiRequest<UnidadeCurricular[]>('/unidades-curriculares')
}

export type Topico = {
  id: string
  uc_id: string
  nome: string
  descricao: string | null
  ordem: number
}

export type TopicoInput = {
  nome: string
  descricao: string | null
}

export const TOPICO_NOME_MAX_LENGTH = 200
export const TOPICO_DESCRICAO_MAX_LENGTH = 1000

export function listTopicos(ucId: string): Promise<Topico[]> {
  return apiRequest<Topico[]>(`/unidades-curriculares/${ucId}/topicos`)
}

export function createTopico(ucId: string, input: TopicoInput): Promise<Topico> {
  return apiRequest<Topico>(`/unidades-curriculares/${ucId}/topicos`, { method: 'POST', body: input })
}

export function updateTopico(id: string, input: TopicoInput): Promise<Topico> {
  return apiRequest<Topico>(`/topicos/${id}`, { method: 'PATCH', body: input })
}

export function reorderTopicos(ucId: string, topicoIds: string[]): Promise<Topico[]> {
  return apiRequest<Topico[]>(`/unidades-curriculares/${ucId}/topicos/ordem`, {
    method: 'PUT',
    body: { topico_ids: topicoIds },
  })
}

export function deleteTopico(id: string): Promise<void> {
  return apiRequest<void>(`/topicos/${id}`, { method: 'DELETE' })
}
