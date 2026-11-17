import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('shows the ApontaUA welcome content', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'ApontaUA' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Frontend inicial' })).toBeInTheDocument()
    expect(screen.getByText(/estrutura React está pronta/i)).toBeInTheDocument()
  })
})
