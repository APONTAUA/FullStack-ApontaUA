import { useId, useState, type FormEvent } from 'react'

import { TOPICO_DESCRICAO_MAX_LENGTH, TOPICO_NOME_MAX_LENGTH, type TopicoInput } from './api'

export type TopicoFormErrors = Partial<Record<'nome', string>>

type Props = {
  initial?: TopicoInput
  submitLabel: string
  busy: boolean
  errors: TopicoFormErrors
  autoFocus?: boolean
  onSubmit: (input: TopicoInput) => void
  onCancel?: () => void
}

export function TopicoForm({ initial, submitLabel, busy, errors, autoFocus, onSubmit, onCancel }: Props) {
  const id = useId()
  const [nome, setNome] = useState(initial?.nome ?? '')
  const [descricao, setDescricao] = useState(initial?.descricao ?? '')
  const [localError, setLocalError] = useState<string | null>(null)
  const nomeErro = localError ?? errors.nome

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const input = { nome: nome.trim(), descricao: descricao.trim() || null }
    if (!input.nome) {
      setLocalError('Indica o nome do tópico.')
      document.getElementById(`${id}-nome`)?.focus()
      return
    }
    setLocalError(null)
    onSubmit(input)
  }

  return (
    <form className="curso-form" onSubmit={handleSubmit} noValidate>
      <div className="field">
        <label htmlFor={`${id}-nome`}>Nome</label>
        <input
          id={`${id}-nome`}
          value={nome}
          maxLength={TOPICO_NOME_MAX_LENGTH}
          autoComplete="off"
          required
          autoFocus={autoFocus}
          aria-invalid={nomeErro ? true : undefined}
          aria-describedby={nomeErro ? `${id}-nome-erro` : `${id}-nome-ajuda`}
          onChange={(event) => setNome(event.target.value)}
        />
        {nomeErro ? (
          <p id={`${id}-nome-erro`} className="field-error">
            {nomeErro}
          </p>
        ) : (
          <p id={`${id}-nome-ajuda`} className="field-help">
            Obrigatório. Não pode repetir outro tópico desta unidade curricular.
          </p>
        )}
      </div>
      <div className="field">
        <label htmlFor={`${id}-descricao`}>Descrição (opcional)</label>
        <textarea
          id={`${id}-descricao`}
          value={descricao}
          maxLength={TOPICO_DESCRICAO_MAX_LENGTH}
          rows={3}
          onChange={(event) => setDescricao(event.target.value)}
        />
      </div>
      <div className="form-actions">
        <button type="submit" className="button button-primary" disabled={busy}>
          {busy ? 'A guardar…' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" className="button" onClick={onCancel} disabled={busy}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  )
}
