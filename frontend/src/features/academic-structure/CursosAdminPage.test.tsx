import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CursosAdminPage } from './CursosAdminPage'
import type { Curso } from './api'

type Handler = (url: string, init: RequestInit) => Response

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

let cursos: Curso[]
let handler: Handler | null
const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
  const url = String(input)
  if (handler) return handler(url, init)
  return json(cursos)
})

beforeEach(() => {
  cursos = [{ id: '1', codigo: '8295', nome: 'Engenharia Informática' }]
  handler = null
  fetchMock.mockClear()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('CursosAdminPage', () => {
  it('lista os cursos', async () => {
    render(<CursosAdminPage canManage />)

    expect(await screen.findByRole('cell', { name: 'Engenharia Informática' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: '8295' })).toBeInTheDocument()
  })

  it('mostra erros junto aos campos e põe o foco no primeiro campo inválido', async () => {
    render(<CursosAdminPage canManage />)
    await screen.findByRole('cell', { name: '8295' })

    fireEvent.click(screen.getByRole('button', { name: 'Adicionar curso' }))

    const codigo = screen.getByLabelText('Código')
    expect(screen.getByText('Indica o código do curso.')).toBeInTheDocument()
    expect(screen.getByText('Indica o nome do curso.')).toBeInTheDocument()
    expect(codigo).toHaveAttribute('aria-invalid', 'true')
    expect(codigo).toHaveFocus()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('cria um curso e anuncia o sucesso', async () => {
    render(<CursosAdminPage canManage />)
    await screen.findByRole('cell', { name: '8295' })
    handler = (url, init) => {
      if (init.method === 'POST') {
        const body = JSON.parse(String(init.body)) as Omit<Curso, 'id'>
        const novo = { id: '2', ...body }
        cursos = [...cursos, novo]
        return json(novo, 201)
      }
      expect(url).toContain('/cursos')
      return json(cursos)
    }

    fireEvent.change(screen.getByLabelText('Código'), { target: { value: ' 9000 ' } })
    fireEvent.change(screen.getByLabelText('Nome'), { target: { value: 'Biologia' } })
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar curso' }))

    expect(await screen.findByRole('cell', { name: 'Biologia' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Curso «Biologia» criado.')
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ codigo: '9000', nome: 'Biologia' })
  })

  it('mostra o código duplicado junto ao campo', async () => {
    render(<CursosAdminPage canManage />)
    await screen.findByRole('cell', { name: '8295' })
    handler = (_url, init) =>
      init.method === 'POST' ? json({ detail: 'duplicate' }, 409) : json(cursos)

    fireEvent.change(screen.getByLabelText('Código'), { target: { value: '8295' } })
    fireEvent.change(screen.getByLabelText('Nome'), { target: { value: 'Outro' } })
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar curso' }))

    expect(await screen.findByText('Já existe um curso com este código.')).toBeInTheDocument()
  })

  it('pede confirmação e explica quando o curso tem associações', async () => {
    render(<CursosAdminPage canManage />)
    await screen.findByRole('cell', { name: '8295' })
    handler = (_url, init) => (init.method === 'DELETE' ? json({ detail: 'associated' }, 409) : json(cursos))

    fireEvent.click(screen.getByRole('button', { name: 'Remover Engenharia Informática' }))
    const confirmacao = screen.getByRole('group', { name: 'Confirmar remoção de Engenharia Informática' })
    fireEvent.click(within(confirmacao).getByRole('button', { name: 'Sim, remover' }))

    expect(await screen.findByText(/tem unidades curriculares associadas/)).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Engenharia Informática' })).toBeInTheDocument()
  })

  it('sem permissão de gestão, mostra só a lista', async () => {
    render(<CursosAdminPage canManage={false} />)

    expect(await screen.findByRole('cell', { name: 'Engenharia Informática' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Adicionar curso' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Editar|^Remover/ })).not.toBeInTheDocument()
  })
})
