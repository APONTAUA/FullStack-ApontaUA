import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { MaterialsSearchPage } from './MaterialsSearchPage'

describe('MaterialsSearchPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('combines the category with the keyword and can remove just the category', async () => {
    const fetchMock = vi.fn(
      async (_input: RequestInfo | URL, _init?: RequestInit) => new Response('[]', { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(<MaterialsSearchPage />)

    for (const label of ['Apontamentos', 'Apresentações', 'Exercícios', 'Exames', 'Soluções', 'Outro']) {
      expect(screen.getByRole('option', { name: label })).toBeInTheDocument()
    }

    fireEvent.change(screen.getByRole('searchbox', { name: 'Palavra-chave' }), {
      target: { value: 'derivadas' },
    })
    fireEvent.change(screen.getByLabelText('Categoria'), { target: { value: 'exame' } })
    fireEvent.click(screen.getByRole('button', { name: 'Pesquisar' }))

    await screen.findByText('Não foram encontrados materiais com estes critérios.')
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/materiais?q=derivadas&categoria=exame'),
      expect.any(Object),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Remover categoria' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('/materiais?q=derivadas'),
        expect.any(Object),
      )
    })
    expect(fetchMock.mock.calls[1]?.[0]).not.toContain('categoria=')
    expect(screen.getByLabelText('Categoria')).toHaveValue('')
  })
})
