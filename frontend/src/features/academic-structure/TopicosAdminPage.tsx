import { useEffect, useState } from 'react'

import { ApiError } from '../../services/api/client'
import {
  createTopico,
  deleteTopico,
  listTopicos,
  listUnidadesCurriculares,
  reorderTopicos,
  updateTopico,
  type Topico,
  type TopicoInput,
  type UnidadeCurricular,
} from './api'
import { TopicoForm, type TopicoFormErrors } from './TopicoForm'

type Props = {
  canManage: boolean
}

type Status = { tone: 'success' | 'error'; text: string } | null

const NOME_REPETIDO = 'Já existe um tópico com este nome nesta unidade curricular.'

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Tens de iniciar sessão para ver os tópicos.'
    if (error.status === 403) return 'Só os administradores podem gerir tópicos.'
    if (error.status === 404) return 'Este tópico ou unidade curricular já não existe. A lista foi atualizada.'
  }
  return 'Não foi possível contactar o servidor. Tenta novamente.'
}

function focusLater(elementId: string) {
  requestAnimationFrame(() => document.getElementById(elementId)?.focus())
}

/** US-019 — gestão de tópicos de uma unidade curricular (RN-031, RN-034). */
export function TopicosAdminPage({ canManage }: Props) {
  const [unidades, setUnidades] = useState<UnidadeCurricular[]>([])
  const [unidadesLoading, setUnidadesLoading] = useState(true)
  const [ucId, setUcId] = useState('')
  const [topicos, setTopicos] = useState<Topico[]>([])
  const [topicosLoading, setTopicosLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [status, setStatus] = useState<Status>(null)
  const [busy, setBusy] = useState(false)
  const [createErrors, setCreateErrors] = useState<TopicoFormErrors>({})
  const [createKey, setCreateKey] = useState(0)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editErrors, setEditErrors] = useState<TopicoFormErrors>({})
  const [confirmingId, setConfirmingId] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    listUnidadesCurriculares()
      .then((data) => {
        if (active) setUnidades(data)
      })
      .catch((error: unknown) => {
        if (active) setLoadError(describeError(error))
      })
      .finally(() => {
        if (active) setUnidadesLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!ucId) return
    let active = true
    listTopicos(ucId)
      .then((data) => {
        if (active) setTopicos(data)
      })
      .catch((error: unknown) => {
        if (active) setLoadError(describeError(error))
      })
      .finally(() => {
        if (active) setTopicosLoading(false)
      })
    return () => {
      active = false
    }
  }, [ucId])

  function chooseUc(next: string) {
    setUcId(next)
    setTopicos([])
    setTopicosLoading(Boolean(next))
    setLoadError(null)
    setStatus(null)
    setEditingId(null)
    setConfirmingId(null)
    setCreateErrors({})
  }

  async function reload() {
    if (!ucId) return
    try {
      setTopicos(await listTopicos(ucId))
    } catch (error) {
      setLoadError(describeError(error))
    }
  }

  async function handleCreate(input: TopicoInput) {
    setBusy(true)
    setStatus(null)
    try {
      const topico = await createTopico(ucId, input)
      setCreateErrors({})
      setCreateKey((key) => key + 1)
      setStatus({ tone: 'success', text: `Tópico «${topico.nome}» criado.` })
      await reload()
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) setCreateErrors({ nome: NOME_REPETIDO })
      else setStatus({ tone: 'error', text: describeError(error) })
    } finally {
      setBusy(false)
    }
  }

  async function handleUpdate(topico: Topico, input: TopicoInput) {
    setBusy(true)
    setStatus(null)
    try {
      const updated = await updateTopico(topico.id, input)
      setEditingId(null)
      setEditErrors({})
      setStatus({ tone: 'success', text: `Tópico «${updated.nome}» atualizado.` })
      await reload()
      focusLater(`editar-${topico.id}`)
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) setEditErrors({ nome: NOME_REPETIDO })
      else {
        setStatus({ tone: 'error', text: describeError(error) })
        if (error instanceof ApiError && error.status === 404) await reload()
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleMove(index: number, delta: -1 | 1) {
    const target = index + delta
    if (target < 0 || target >= topicos.length) return
    const ids = topicos.map((topico) => topico.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    const moved = topicos[index]
    setBusy(true)
    setStatus(null)
    try {
      setTopicos(await reorderTopicos(ucId, ids))
      setStatus({ tone: 'success', text: `«${moved.nome}» passou para a posição ${target + 1} de ${ids.length}.` })
      const keepDirection = (delta === -1 && target > 0) || (delta === 1 && target < ids.length - 1)
      const direction = keepDirection ? delta : -delta
      focusLater(`${direction === -1 ? 'subir' : 'descer'}-${moved.id}`)
    } catch (error) {
      setStatus({ tone: 'error', text: describeError(error) })
      await reload()
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(topico: Topico) {
    setBusy(true)
    setStatus(null)
    try {
      await deleteTopico(topico.id)
      setStatus({ tone: 'success', text: `Tópico «${topico.nome}» removido.` })
    } catch (error) {
      const text =
        error instanceof ApiError && error.status === 409
          ? `O tópico «${topico.nome}» tem notas de estudo associadas e não pode ser removido.`
          : describeError(error)
      setStatus({ tone: 'error', text })
    } finally {
      setConfirmingId(null)
      setBusy(false)
      await reload()
    }
  }

  const ucSelecionada = unidades.find((uc) => uc.id === ucId)

  return (
    <section aria-labelledby="topicos-titulo" className="card">
      <h2 id="topicos-titulo">Tópicos</h2>
      <p className="section-intro">
        Os tópicos agrupam as notas de estudo de cada unidade curricular, por assunto ou componente.
      </p>

      <div className={`status ${status ? `status-${status.tone}` : ''}`} role="status" aria-live="polite">
        {status?.text}
      </div>

      {loadError && (
        <div className="status status-error" role="alert">
          {loadError}
        </div>
      )}

      {unidadesLoading && <p>A carregar as unidades curriculares…</p>}
      {!unidadesLoading && !loadError && unidades.length === 0 && (
        <p>Ainda não há unidades curriculares registadas.</p>
      )}

      {unidades.length > 0 && (
        <div className="field subsection uc-select">
          <label htmlFor="topicos-uc">Unidade curricular</label>
          <select id="topicos-uc" value={ucId} onChange={(event) => chooseUc(event.target.value)}>
            <option value="">Escolhe uma unidade curricular</option>
            {unidades.map((uc) => (
              <option key={uc.id} value={uc.id}>
                {uc.codigo} — {uc.nome}
              </option>
            ))}
          </select>
        </div>
      )}

      {ucSelecionada && (
        <>
          {canManage && (
            <section aria-labelledby="novo-topico-titulo" className="subsection">
              <h3 id="novo-topico-titulo">Adicionar tópico a {ucSelecionada.nome}</h3>
              <TopicoForm
                key={`${ucId}-${createKey}`}
                submitLabel="Adicionar tópico"
                busy={busy}
                errors={createErrors}
                onSubmit={(input) => void handleCreate(input)}
              />
            </section>
          )}

          <section aria-labelledby="lista-topicos-titulo" className="subsection">
            <h3 id="lista-topicos-titulo">Tópicos de {ucSelecionada.nome}</h3>
            {topicosLoading && <p>A carregar os tópicos…</p>}
            {!topicosLoading && topicos.length === 0 && <p>Esta unidade curricular ainda não tem tópicos.</p>}
            {topicos.length > 0 && (
              <ol className="topic-list">
                {topicos.map((topico, index) => (
                  <li key={topico.id} className="topic-item">
                    {editingId === topico.id ? (
                      <TopicoForm
                        initial={{ nome: topico.nome, descricao: topico.descricao }}
                        submitLabel="Guardar alterações"
                        busy={busy}
                        errors={editErrors}
                        autoFocus
                        onSubmit={(input) => void handleUpdate(topico, input)}
                        onCancel={() => {
                          setEditingId(null)
                          setEditErrors({})
                          focusLater(`editar-${topico.id}`)
                        }}
                      />
                    ) : (
                      <>
                        <div className="topic-text">
                          <strong>{topico.nome}</strong>
                          {topico.descricao && <p>{topico.descricao}</p>}
                        </div>
                        {canManage &&
                          (confirmingId === topico.id ? (
                            <div
                              className="row-actions"
                              role="group"
                              aria-label={`Confirmar remoção de ${topico.nome}`}
                            >
                              <span>Remover este tópico?</span>
                              <button
                                type="button"
                                className="button button-danger"
                                disabled={busy}
                                autoFocus
                                onClick={() => void handleDelete(topico)}
                              >
                                Sim, remover
                              </button>
                              <button
                                type="button"
                                className="button"
                                disabled={busy}
                                onClick={() => {
                                  setConfirmingId(null)
                                  focusLater(`remover-${topico.id}`)
                                }}
                              >
                                Não
                              </button>
                            </div>
                          ) : (
                            <div className="row-actions">
                              <button
                                type="button"
                                id={`subir-${topico.id}`}
                                className="button"
                                disabled={busy || index === 0}
                                aria-label={`Subir ${topico.nome}`}
                                onClick={() => void handleMove(index, -1)}
                              >
                                ↑ Subir
                              </button>
                              <button
                                type="button"
                                id={`descer-${topico.id}`}
                                className="button"
                                disabled={busy || index === topicos.length - 1}
                                aria-label={`Descer ${topico.nome}`}
                                onClick={() => void handleMove(index, 1)}
                              >
                                ↓ Descer
                              </button>
                              <button
                                type="button"
                                id={`editar-${topico.id}`}
                                className="button"
                                disabled={busy}
                                aria-label={`Editar ${topico.nome}`}
                                onClick={() => {
                                  setConfirmingId(null)
                                  setEditErrors({})
                                  setEditingId(topico.id)
                                }}
                              >
                                Editar
                              </button>
                              <button
                                type="button"
                                id={`remover-${topico.id}`}
                                className="button"
                                disabled={busy}
                                aria-label={`Remover ${topico.nome}`}
                                onClick={() => {
                                  setEditingId(null)
                                  setConfirmingId(topico.id)
                                }}
                              >
                                Remover
                              </button>
                            </div>
                          ))}
                      </>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>
        </>
      )}
    </section>
  )
}
