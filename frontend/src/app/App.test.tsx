import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

describe('App', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('shows the ApontaUA heading and the degree programme page', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('[]', { status: 200 })))

    render(<App />)

    expect(screen.getByRole('heading', { name: 'ApontaUA' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Cursos' })).toBeInTheDocument()
    expect(await screen.findByText('Ainda não há cursos registados.')).toBeInTheDocument()
  })

  it('muda entre as secções Cursos e Tópicos', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('[]', { status: 200 })))

    render(<App />)
    const topicos = screen.getByRole('button', { name: 'Tópicos' })
    fireEvent.click(topicos)

    expect(topicos).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: 'Cursos' })).not.toHaveAttribute('aria-current')
    expect(screen.getByRole('heading', { name: 'Tópicos' })).toBeInTheDocument()
    expect(await screen.findByText('Ainda não há unidades curriculares registadas.')).toBeInTheDocument()
  })
})
