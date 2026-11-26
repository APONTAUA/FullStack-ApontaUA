import { useState } from 'react'

import { CursosAdminPage } from '../features/academic-structure/CursosAdminPage'
import { TopicosAdminPage } from '../features/academic-structure/TopicosAdminPage'
import { DEV_ROLES, getDevRole, setDevRole, type DevRole } from '../services/api/client'

type Secao = 'cursos' | 'topicos'

const SECOES: { id: Secao; label: string }[] = [
  { id: 'cursos', label: 'Cursos' },
  { id: 'topicos', label: 'Tópicos' },
]

export function App() {
  const [role, setRole] = useState<DevRole>(getDevRole())
  const [secao, setSecao] = useState<Secao>('cursos')
  const canManage = role === 'administrador'

  function changeRole(next: DevRole) {
    setDevRole(next)
    setRole(next)
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <p className="app-eyebrow">Universidade de Aveiro</p>
        <h1>ApontaUA</h1>
      </header>

      {import.meta.env.DEV && (
        <aside className="dev-panel" aria-label="Opções de desenvolvimento">
          <label htmlFor="dev-role">Papel simulado (só em desenvolvimento)</label>
          <select id="dev-role" value={role} onChange={(event) => changeRole(event.target.value as DevRole)}>
            {DEV_ROLES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </aside>
      )}

      <nav aria-label="Estrutura académica" className="section-nav">
        <ul>
          {SECOES.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="button"
                aria-current={secao === item.id ? 'page' : undefined}
                onClick={() => setSecao(item.id)}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* A key obriga a recarregar os dados com o novo papel. */}
      {secao === 'cursos' ? (
        <CursosAdminPage key={role} canManage={canManage} />
      ) : (
        <TopicosAdminPage key={role} canManage={canManage} />
      )}
    </main>
  )
}
