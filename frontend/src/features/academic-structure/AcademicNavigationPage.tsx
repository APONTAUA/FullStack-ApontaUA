import { useEffect, useState } from 'react'

import { ApiError } from '../../services/api/client'
import { listMateriaisPorTopico, type Material } from '../materials/api'
import {
  listCursos,
  listUnidadesCurriculares,
  listTopicosPorUC,
  type Curso,
  type UnidadeCurricular,
  type Topico,
} from './api'

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Tens de iniciar sessão para consultar a estrutura académica.'
    if (error.status === 403) return 'Não tens permissão para consultar esta informação.'
    if (error.status === 404) return 'O elemento selecionado já não existe.'
  }
  return 'Não foi possível contactar o servidor. Tenta novamente.'
}

export function AcademicNavigationPage() {
  const [cursos, setCursos] = useState<Curso[]>([])
  const [unidades, setUnidades] = useState<UnidadeCurricular[]>([])
  const [topicos, setTopicos] = useState<Topico[]>([])
  const [materiais, setMateriais] = useState<Material[]>([])

  const [cursoSelecionado, setCursoSelecionado] = useState<string | null>(null)
  const [ucSelecionada, setUcSelecionada] = useState<string | null>(null)
  const [topicoSelecionado, setTopicoSelecionado] = useState<string | null>(null)

  const [loading, setLoading] = useState(true)
  const [loadingTopicos, setLoadingTopicos] = useState(false)
  const [loadingMateriais, setLoadingMateriais] = useState(false)

  const [erro, setErro] = useState<string | null>(null)
  const [erroTopicos, setErroTopicos] = useState<string | null>(null)
  const [erroMateriais, setErroMateriais] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function carregarEstrutura() {
      try {
        const [listaCursos, listaUnidades] = await Promise.all([
          listCursos(),
          listUnidadesCurriculares(),
        ])

        if (active) {
          setCursos(listaCursos)
          setUnidades(listaUnidades)
          setErro(null)
        }
      } catch (error) {
        if (active) setErro(describeError(error))
      } finally {
        if (active) setLoading(false)
      }
    }

    void carregarEstrutura()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!ucSelecionada) {
      setTopicos([])
      return
    }

    let active = true

    async function carregarTopicos() {
      setLoadingTopicos(true)
      setErroTopicos(null)

      try {
        const lista = await listTopicosPorUC(ucSelecionada!)
        if (active) setTopicos(lista)
      } catch (error) {
        if (active) setErroTopicos(describeError(error))
      } finally {
        if (active) setLoadingTopicos(false)
      }
    }

    void carregarTopicos()

    return () => {
      active = false
    }
  }, [ucSelecionada])

  useEffect(() => {
    if (!topicoSelecionado) {
      setMateriais([])
      return
    }

    let active = true

    async function carregarMateriais() {
      setLoadingMateriais(true)
      setErroMateriais(null)

      try {
        const lista = await listMateriaisPorTopico(topicoSelecionado!)
        if (active) setMateriais(lista)
      } catch (error) {
        if (active) setErroMateriais(describeError(error))
      } finally {
        if (active) setLoadingMateriais(false)
      }
    }

    void carregarMateriais()

    return () => {
      active = false
    }
  }, [topicoSelecionado])

  const unidadesDoCurso = unidades.filter(
    (uc) => uc.curso_id === cursoSelecionado,
  )

  const associacoesDisponiveis =
    unidades.length > 0 && unidades.every((uc) => 'curso_id' in uc)

  const cursoAtual = cursos.find((curso) => curso.id === cursoSelecionado)
  const ucAtual = unidades.find((uc) => uc.id === ucSelecionada)
  const topicoAtual = topicos.find((topico) => topico.id === topicoSelecionado)

  function selecionarCurso(id: string) {
    setCursoSelecionado(id)
    setUcSelecionada(null)
    setTopicoSelecionado(null)
    setTopicos([])
    setMateriais([])
  }

  function selecionarUC(id: string) {
    setUcSelecionada(id)
    setTopicoSelecionado(null)
    setMateriais([])
  }

  return (
    <section aria-labelledby="academic-navigation-title" className="card academic-navigation">
      <h2 id="academic-navigation-title">Navegação académica</h2>
      <p className="section-intro">
        Explora os cursos, unidades curriculares, tópicos e materiais de estudo
        disponíveis na plataforma ApontaUA.
      </p>

      {loading && <p role="status">A carregar a estrutura académica...</p>}

      {erro && (
        <div className="status status-error" role="alert">
          {erro}
          <button
            type="button"
            className="button button-link"
            onClick={() => window.location.reload()}
          >
            Tentar novamente
          </button>
        </div>
      )}

      {!loading && !erro && (
        <>
          <section className="subsection" aria-labelledby="navigation-courses">
            <h3 id="navigation-courses">1. Cursos</h3>

            {cursos.length === 0 && <p>Ainda não existem cursos disponíveis.</p>}

            <div className="academic-options">
              {cursos.map((curso) => (
                <button
                  key={curso.id}
                  type="button"
                  className={`academic-option ${cursoSelecionado === curso.id ? 'academic-option-selected' : ''}`}
                  aria-pressed={cursoSelecionado === curso.id}
                  onClick={() => selecionarCurso(curso.id)}
                >
                  <strong>{curso.nome}</strong>
                  <span>{curso.codigo}</span>
                </button>
              ))}
            </div>
          </section>

          {cursoAtual && (
            <section className="subsection" aria-labelledby="navigation-units">
              <h3 id="navigation-units">2. Unidades curriculares</h3>
              <p>Curso selecionado: <strong>{cursoAtual.nome}</strong></p>

              {!associacoesDisponiveis && (
                <p className="navigation-notice" role="status">
                  A consulta das associações entre cursos e unidades curriculares
                  depende da integração da US-017.
                </p>
              )}

              {associacoesDisponiveis && unidadesDoCurso.length === 0 && (
                <p>Este curso ainda não tem unidades curriculares associadas.</p>
              )}

              <div className="academic-options">
                {unidadesDoCurso.map((uc) => (
                  <button
                    key={uc.id}
                    type="button"
                    className={`academic-option ${ucSelecionada === uc.id ? 'academic-option-selected' : ''}`}
                    aria-pressed={ucSelecionada === uc.id}
                    onClick={() => selecionarUC(uc.id)}
                  >
                    <strong>{uc.nome}</strong>
                    <span>{uc.codigo}</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {ucAtual && (
            <section className="subsection" aria-labelledby="navigation-topics">
              <h3 id="navigation-topics">3. Tópicos</h3>
              <p>Unidade curricular selecionada: <strong>{ucAtual.nome}</strong></p>

              {loadingTopicos && <p role="status">A carregar tópicos...</p>}
              {erroTopicos && <p className="status status-error" role="alert">{erroTopicos}</p>}

              {!loadingTopicos && !erroTopicos && topicos.length === 0 && (
                <p>Esta unidade curricular ainda não tem tópicos.</p>
              )}

              <div className="academic-options">
                {topicos.map((topico) => (
                  <button
                    key={topico.id}
                    type="button"
                    className={`academic-option ${topicoSelecionado === topico.id ? 'academic-option-selected' : ''}`}
                    aria-pressed={topicoSelecionado === topico.id}
                    onClick={() => setTopicoSelecionado(topico.id)}
                  >
                    <strong>{topico.nome}</strong>
                    {topico.descricao && <span>{topico.descricao}</span>}
                  </button>
                ))}
              </div>
            </section>
          )}

          {topicoAtual && (
            <section className="subsection" aria-labelledby="navigation-materials">
              <h3 id="navigation-materials">4. Notas de estudo</h3>
              <p>Tópico selecionado: <strong>{topicoAtual.nome}</strong></p>

              {loadingMateriais && <p role="status">A carregar materiais...</p>}
              {erroMateriais && <p className="status status-error" role="alert">{erroMateriais}</p>}

              {!loadingMateriais && !erroMateriais && materiais.length === 0 && (
                <p>Ainda não existem notas de estudo publicadas neste tópico.</p>
              )}

              {!loadingMateriais && !erroMateriais && materiais.map((material) => (
                <article key={material.id} className="academic-material">
                  <h4>{material.titulo}</h4>
                  {material.descricao && <p>{material.descricao}</p>}
                  <p>
                    <strong>Categoria:</strong> {material.categoria}
                  </p>
                  {material.ano_letivo && (
                    <p><strong>Ano letivo:</strong> {material.ano_letivo}</p>
                  )}
                  <p>
                    <strong>Ficheiro:</strong> {material.versao_atual.ficheiro.nome_original}
                  </p>
                  <p>
                    <strong>Publicado em:</strong>{' '}
                    {new Date(material.publicado_em).toLocaleDateString('pt-PT')}
                  </p>
                </article>
              ))}
            </section>
          )}
        </>
      )}

      <p className="navigation-notice">
        A organização das unidades curriculares por ano curricular e semestre
        será integrada com a US-018.
      </p>
    </section>
  )
}
