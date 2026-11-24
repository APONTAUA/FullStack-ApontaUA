import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { TopicosAdminPage } from './TopicosAdminPage'
import type { Topico, UnidadeCurricular } from './api'

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

const UC: UnidadeCurricular = { id: 'uc1', codigo: '40337', nome: 'PEI' }
let unidades: UnidadeCurricular[]
let topicos: Topico[]
let override: ((url: string, init: RequestInit) => Response | undefined) | null

const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
  const url = String(input)
  const custom = override?.(url, init)
  if (custom) return custom
  if (url.endsWith('/unidades-curriculares')) return json(unidades)
  if (url.endsWith('/topicos/ordem') && init.method === 'PUT') {
    const { topico_ids } = JSON.parse(String(init.body)) as { topico_ids: string[] }
    topicos = topico_ids.map((id, ordem) => ({ ...topicos.find((t) => t.id === id)!, ordem }))
    return json(topicos)
  }
  if (url.endsWith('/topicos') && init.method === 'POST') {
    const body = JSON.parse(String(init.body)) as { nome: string; descricao: string | null }
    const novo = { id: `t${topicos.length + 1}`, uc_id: 'uc1', ordem: topicos.length, ...body }
    topicos = [...topicos, novo]
    return json(novo, 201)
  }
  if (url.endsWith('/topicos')) return json(topicos)
  return json({ detail: 'not found' }, 404)
})

beforeEach(() => {
  unidades = [UC]
  topicos = [
    { id: 't1', uc_id: 'uc1', nome: 'Requisitos', descricao: 'Levantamento', ordem: 0 },
    { id: 't2', uc_id: 'uc1', nome: 'Arquitetura', descricao: null, ordem: 1 },
  ]
  override = null
  fetchMock.mockClear()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

async function escolherUc() {
  fireEvent.change(await screen.findByLabelText('Unidade curricular'), { target: { value: 'uc1' } })
  await screen.findByText('Requisitos')
}

describe('TopicosAdminPage', () => {
  it('mostra os tópicos da unidade curricular escolhida, pela ordem', async () => {
    render(<TopicosAdminPage canManage />)
    await escolherUc()

    const itens = within(screen.getByRole('list')).getAllByRole('listitem')
    expect(itens.map((item) => item.querySelector('strong')?.textContent)).toEqual(['Requisitos', 'Arquitetura'])
    expect(screen.getByText('Levantamento')).toBeInTheDocument()
  })

  it('avisa quando não há unidades curriculares', async () => {
    unidades = []
    render(<TopicosAdminPage canManage />)
    expect(await screen.findByText('Ainda não há unidades curriculares registadas.')).toBeInTheDocument()
  })

  it('valida o nome e põe o foco no campo', async () => {
    render(<TopicosAdminPage canManage />)
    await escolherUc()

    fireEvent.click(screen.getByRole('button', { name: 'Adicionar tópico' }))

    const nome = screen.getAllByLabelText('Nome')[0]
    expect(screen.getByText('Indica o nome do tópico.')).toBeInTheDocument()
    expect(nome).toHaveAttribute('aria-invalid', 'true')
    expect(nome).toHaveFocus()
  })

  it('cria um tópico e anuncia o sucesso', async () => {
    render(<TopicosAdminPage canManage />)
    await escolherUc()

    fireEvent.change(screen.getAllByLabelText('Nome')[0], { target: { value: ' Testes ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar tópico' }))

    expect(await screen.findByText('Testes')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Tópico «Testes» criado.')
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ nome: 'Testes', descricao: null })
  })

  it('mostra o nome repetido junto ao campo', async () => {
    override = (_url, init) => (init.method === 'POST' ? json({ detail: 'duplicate' }, 409) : undefined)
    render(<TopicosAdminPage canManage />)
    await escolherUc()

    fireEvent.change(screen.getAllByLabelText('Nome')[0], { target: { value: 'Requisitos' } })
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar tópico' }))

    expect(
      await screen.findByText('Já existe um tópico com este nome nesta unidade curricular.'),
    ).toBeInTheDocument()
  })

  it('reordena os tópicos com os botões subir e descer', async () => {
    render(<TopicosAdminPage canManage />)
    await escolherUc()

    expect(screen.getByRole('button', { name: 'Subir Requisitos' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Descer Requisitos' }))

    expect(await screen.findByText('«Requisitos» passou para a posição 2 de 2.')).toBeInTheDocument()
    const put = fetchMock.mock.calls.find(([, init]) => init?.method === 'PUT')
    expect(JSON.parse(String(put?.[1]?.body))).toEqual({ topico_ids: ['t2', 't1'] })
    const itens = within(screen.getByRole('list')).getAllByRole('listitem')
    expect(itens[0]).toHaveTextContent('Arquitetura')
  })

  it('explica quando o tópico tem notas de estudo', async () => {
    override = (_url, init) => (init.method === 'DELETE' ? json({ detail: 'notes' }, 409) : undefined)
    render(<TopicosAdminPage canManage />)
    await escolherUc()

    fireEvent.click(screen.getByRole('button', { name: 'Remover Requisitos' }))
    const grupo = screen.getByRole('group', { name: 'Confirmar remoção de Requisitos' })
    fireEvent.click(within(grupo).getByRole('button', { name: 'Sim, remover' }))

    expect(await screen.findByText(/tem notas de estudo associadas/)).toBeInTheDocument()
  })

  it('sem permissão de gestão, mostra só a lista', async () => {
    render(<TopicosAdminPage canManage={false} />)
    await escolherUc()

    expect(screen.queryByRole('button', { name: 'Adicionar tópico' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^(Subir|Descer|Editar|Remover)/ })).not.toBeInTheDocument()
  })
})
