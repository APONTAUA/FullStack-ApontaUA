import { useState } from 'react'

import { CursosAdminPage } from '../features/academic-structure/CursosAdminPage'
import { DEV_ROLES, getDevRole, setDevRole, type DevRole } from '../services/api/client'
import { AcademicNavigationPage } from '../features/academic-structure/AcademicNavigationPage'

export function App() {
  const [role, setRole] = useState<DevRole>(getDevRole())

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

      {/* A key obriga a recarregar a lista com o novo papel. */}
    <>
      <AcademicNavigationPage />

      <CursosAdminPage key={role} canManage={role === 'administrador'} />
    </>
    </main>
  )
}
