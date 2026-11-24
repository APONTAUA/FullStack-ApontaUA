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
