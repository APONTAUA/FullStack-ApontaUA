import { useState, type FormEvent } from 'react'

import { ApiError } from '../../services/api/client'
import {
  CATEGORIAS_MATERIAL,
  pesquisarMateriais,
  type CategoriaMaterial,
  type Material,
} from './api'

function describeError(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return 'Tens de iniciar sessão para pesquisar materiais.'
  }
  if (error instanceof ApiError && error.status === 403) {
    return 'Não tens permissão para pesquisar materiais.'
  }
  return 'Não foi possível pesquisar materiais. Tenta novamente.'
}

export function MaterialsSearchPage() {
  const [termo, setTermo] = useState('')
  const [categoria, setCategoria] = useState<CategoriaMaterial | ''>('')
  const [materiais, setMateriais] = useState<Material[]>([])
  const [pesquisaRealizada, setPesquisaRealizada] = useState(false)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function pesquisar(
    event?: FormEvent<HTMLFormElement>,
    categoriaSelecionada: CategoriaMaterial | '' = categoria,
  ) {
    event?.preventDefault()
    setLoading(true)
    setErro(null)
    try {
      setMateriais(
        await pesquisarMateriais({
          q: termo.trim() || undefined,
          categoria: categoriaSelecionada || undefined,
        }),
      )
      setPesquisaRealizada(true)
    } catch (error) {
      setErro(describeError(error))
    } finally {
      setLoading(false)
    }
  }

  function limparCategoria() {
    setCategoria('')
    void pesquisar(undefined, '')
  }

  return (
    <section aria-labelledby="materials-search-title" className="card">
      <h2 id="materials-search-title">Pesquisar materiais</h2>
      <p className="section-intro">
        Encontra recursos académicos por palavra-chave e categoria.
      </p>

      <form className="materials-search-form" onSubmit={(event) => void pesquisar(event)}>
        <div className="field">
          <label htmlFor="materials-search-term">Palavra-chave</label>
          <input
            id="materials-search-term"
            type="search"
            maxLength={200}
            value={termo}
            onChange={(event) => setTermo(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="materials-search-category">Categoria</label>
          <select
            id="materials-search-category"
            value={categoria}
            onChange={(event) => setCategoria(event.target.value as CategoriaMaterial | '')}
          >
            <option value="">Todas as categorias</option>
            {CATEGORIAS_MATERIAL.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-actions">
          <button type="submit" className="button button-primary" disabled={loading}>
            Pesquisar
          </button>
          {categoria && (
            <button type="button" className="button" disabled={loading} onClick={limparCategoria}>
              Remover categoria
            </button>
          )}
        </div>
      </form>

      {loading && <p role="status">A pesquisar materiais...</p>}
      {erro && <p className="status status-error" role="alert">{erro}</p>}

      {pesquisaRealizada && !loading && !erro && materiais.length === 0 && (
        <p role="status">Não foram encontrados materiais com estes critérios.</p>
      )}

      {materiais.length > 0 && (
        <div className="materials-search-results" aria-live="polite">
          {materiais.map((material) => {
            const label = CATEGORIAS_MATERIAL.find(
              (option) => option.value === material.categoria,
            )?.label ?? material.categoria
            return (
              <article key={material.id} className="academic-material">
                <h3>{material.titulo}</h3>
                {material.descricao && <p>{material.descricao}</p>}
                <p><strong>Categoria:</strong> {label}</p>
                {material.ano_letivo && <p><strong>Ano letivo:</strong> {material.ano_letivo}</p>}
                <p><strong>Ficheiro:</strong> {material.versao_atual.ficheiro.nome_original}</p>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
