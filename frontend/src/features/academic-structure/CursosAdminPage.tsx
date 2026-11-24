import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '../../services/api/client'
import { createCurso, deleteCurso, listCursos, updateCurso, type Curso, type CursoInput } from './api'
import { CursoForm, type CursoFormErrors } from './CursoForm'

type Props = {
  canManage: boolean
}

type Status = { tone: 'success' | 'error'; text: string } | null

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Tens de iniciar sessão para ver os cursos.'
    if (error.status === 403) return 'Só os administradores podem gerir cursos.'
    if (error.status === 404) return 'Este curso já não existe. A lista foi atualizada.'
  }
  return 'Não foi possível contactar o servidor. Tenta novamente.'
}

/** US-015 — gestão de cursos (RF-016). */
export function CursosAdminPage({ canManage }: Props) {
  const [cursos, setCursos] = useState<Curso[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [status, setStatus] = useState<Status>(null)
  const [busy, setBusy] = useState(false)
  const [createErrors, setCreateErrors] = useState<CursoFormErrors>({})
  const [createKey, setCreateKey] = useState(0)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editErrors, setEditErrors] = useState<CursoFormErrors>({})
  const [confirmingId, setConfirmingId] = useState<string | null>(null)

  const reload = useCallback(async () => {
    try {
      setCursos(await listCursos())
      setLoadError(null)
    } catch (error) {
      setLoadError(describeError(error))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    listCursos()
      .then((data) => {
        if (active) setCursos(data)
      })
      .catch((error: unknown) => {
        if (active) setLoadError(describeError(error))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  async function handleCreate(input: CursoInput) {
    setBusy(true)
    setStatus(null)
    try {
      const curso = await createCurso(input)
      setCreateErrors({})
      setCreateKey((key) => key + 1)
      setStatus({ tone: 'success', text: `Curso «${curso.nome}» criado.` })
      await reload()
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setCreateErrors({ codigo: 'Já existe um curso com este código.' })
      } else {
        setStatus({ tone: 'error', text: describeError(error) })
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleUpdate(curso: Curso, input: CursoInput) {
    setBusy(true)
    setStatus(null)
    try {
      const updated = await updateCurso(curso.id, input)
      setEditingId(null)
      setEditErrors({})
      setStatus({ tone: 'success', text: `Curso «${updated.nome}» atualizado.` })
      await reload()
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setEditErrors({ codigo: 'Já existe um curso com este código.' })
      } else {
        setStatus({ tone: 'error', text: describeError(error) })
        if (error instanceof ApiError && error.status === 404) await reload()
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(curso: Curso) {
    setBusy(true)
    setStatus(null)
    try {
      await deleteCurso(curso.id)
      setStatus({ tone: 'success', text: `Curso «${curso.nome}» removido.` })
    } catch (error) {
      const text =
        error instanceof ApiError && error.status === 409
          ? `O curso «${curso.nome}» tem unidades curriculares associadas. Remove primeiro essas ligações.`
          : describeError(error)
      setStatus({ tone: 'error', text })
    } finally {
      setConfirmingId(null)
      setBusy(false)
      await reload()
    }
  }

  return (
    <section aria-labelledby="cursos-titulo" className="card">
      <h2 id="cursos-titulo">Cursos</h2>
      <p className="section-intro">
        Os cursos são o primeiro nível da estrutura académica: as unidades curriculares, os tópicos e os
        materiais organizam-se a partir deles.
      </p>

      <div className={`status ${status ? `status-${status.tone}` : ''}`} role="status" aria-live="polite">
        {status?.text}
      </div>

      {canManage && (
        <section aria-labelledby="novo-curso-titulo" className="subsection">
          <h3 id="novo-curso-titulo">Adicionar curso</h3>
          <CursoForm
            key={createKey}
            submitLabel="Adicionar curso"
            busy={busy}
            errors={createErrors}
            onSubmit={handleCreate}
          />
        </section>
      )}

      <section aria-labelledby="lista-cursos-titulo" className="subsection">
        <h3 id="lista-cursos-titulo">Cursos registados</h3>
        {loading && <p>A carregar os cursos…</p>}
        {loadError && (
          <div className="status status-error" role="alert">
            {loadError}{' '}
            <button type="button" className="button button-link" onClick={() => void reload()}>
              Tentar novamente
            </button>
          </div>
        )}
        {!loading && !loadError && cursos.length === 0 && <p>Ainda não há cursos registados.</p>}
        {cursos.length > 0 && (
          <table className="data-table">
            <caption className="visually-hidden">Cursos registados, por ordem alfabética</caption>
            <thead>
              <tr>
                <th scope="col">Código</th>
                <th scope="col">Nome</th>
                {canManage && <th scope="col">Ações</th>}
              </tr>
            </thead>
            <tbody>
              {cursos.map((curso) =>
                editingId === curso.id ? (
                  <tr key={curso.id}>
                    <td colSpan={3}>
                      <h4 className="visually-hidden">Editar {curso.nome}</h4>
                      <CursoForm
                        initial={curso}
                        submitLabel="Guardar alterações"
                        busy={busy}
                        errors={editErrors}
                        autoFocus
                        onSubmit={(input) => void handleUpdate(curso, input)}
                        onCancel={() => {
                          setEditingId(null)
                          setEditErrors({})
                        }}
                      />
                    </td>
                  </tr>
                ) : (
                  <tr key={curso.id}>
                    <td>{curso.codigo}</td>
                    <td>{curso.nome}</td>
                    {canManage && (
                      <td>
                        {confirmingId === curso.id ? (
                          <div className="row-actions" role="group" aria-label={`Confirmar remoção de ${curso.nome}`}>
                            <span>Remover este curso?</span>
                            <button
                              type="button"
                              className="button button-danger"
                              disabled={busy}
                              autoFocus
                              onClick={() => void handleDelete(curso)}
                            >
                              Sim, remover
                            </button>
                            <button type="button" className="button" disabled={busy} onClick={() => setConfirmingId(null)}>
                              Não
                            </button>
                          </div>
                        ) : (
                          <div className="row-actions">
                            <button
                              type="button"
                              className="button"
                              disabled={busy}
                              aria-label={`Editar ${curso.nome}`}
                              onClick={() => {
                                setConfirmingId(null)
                                setEditErrors({})
                                setEditingId(curso.id)
                              }}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className="button"
                              disabled={busy}
                              aria-label={`Remover ${curso.nome}`}
                              onClick={() => {
                                setEditingId(null)
                                setConfirmingId(curso.id)
                              }}
                            >
                              Remover
                            </button>
                          </div>
                        )}
                      </td>
                    )}
                  </tr>
                ),
              )}
            </tbody>
          </table>
        )}
      </section>
    </section>
  )
}
