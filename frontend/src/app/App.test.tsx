import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the ApontaUA heading and the degree programme page', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('[]', { status: 200 })))

    render(<App />)

    expect(screen.getByRole('heading', { name: 'ApontaUA' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Cursos' })).toBeInTheDocument()
    expect(await screen.findByText('Ainda não há cursos registados.')).toBeInTheDocument()
  })
})
