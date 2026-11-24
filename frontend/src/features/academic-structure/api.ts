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

export type UnidadeCurricular = {
  id: string
  codigo: string
  nome: string
  curso_id?: string | null
}

export type Topico = {
  id: string
  uc_id: string
  nome: string
  descricao: string | null
  ordem: number
}

export const CODIGO_MAX_LENGTH = 20
export const NOME_MAX_LENGTH = 200

// US-015 — Cursos

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

// US-021 — Unidades curriculares

export function listUnidadesCurriculares(): Promise<UnidadeCurricular[]> {
  return apiRequest<UnidadeCurricular[]>('/unidades-curriculares')
}

// US-021 — Tópicos de uma unidade curricular

export function listTopicosPorUC(ucId: string): Promise<Topico[]> {
  return apiRequest<Topico[]>(
    `/unidades-curriculares/${encodeURIComponent(ucId)}/topicos`,
  )
}