import { useId, useState, type FormEvent } from 'react'

import { CODIGO_MAX_LENGTH, NOME_MAX_LENGTH, type CursoInput } from './api'

export type CursoFormErrors = Partial<Record<keyof CursoInput, string>>

type Props = {
  initial?: CursoInput
  submitLabel: string
  busy: boolean
  errors: CursoFormErrors
  autoFocus?: boolean
  onSubmit: (input: CursoInput) => void
  onCancel?: () => void
}

function validate(input: CursoInput): CursoFormErrors {
  const errors: CursoFormErrors = {}
  if (!input.codigo) errors.codigo = 'Indica o código do curso.'
  if (!input.nome) errors.nome = 'Indica o nome do curso.'
  return errors
}

export function CursoForm({ initial, submitLabel, busy, errors, autoFocus, onSubmit, onCancel }: Props) {
  const id = useId()
  const [codigo, setCodigo] = useState(initial?.codigo ?? '')
  const [nome, setNome] = useState(initial?.nome ?? '')
  const [localErrors, setLocalErrors] = useState<CursoFormErrors>({})
  const shown = { ...errors, ...localErrors }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const input = { codigo: codigo.trim(), nome: nome.trim() }
    const found = validate(input)
    setLocalErrors(found)
    if (Object.keys(found).length > 0) {
      const firstInvalid = found.codigo ? `${id}-codigo` : `${id}-nome`
      document.getElementById(firstInvalid)?.focus()
      return
    }
    onSubmit(input)
  }

  return (
    <form className="curso-form" onSubmit={handleSubmit} noValidate>
      <p className="form-hint">Os dois campos são obrigatórios.</p>
      <div className="field">
        <label htmlFor={`${id}-codigo`}>Código</label>
        <input
          id={`${id}-codigo`}
          value={codigo}
          maxLength={CODIGO_MAX_LENGTH}
          autoComplete="off"
          required
          autoFocus={autoFocus}
          aria-invalid={shown.codigo ? true : undefined}
          aria-describedby={shown.codigo ? `${id}-codigo-erro` : `${id}-codigo-ajuda`}
          onChange={(event) => setCodigo(event.target.value)}
        />
        {shown.codigo ? (
          <p id={`${id}-codigo-erro`} className="field-error">
            {shown.codigo}
          </p>
        ) : (
          <p id={`${id}-codigo-ajuda`} className="field-help">
            Código oficial da UA, até {CODIGO_MAX_LENGTH} caracteres. Tem de ser único.
          </p>
        )}
      </div>
      <div className="field">
        <label htmlFor={`${id}-nome`}>Nome</label>
        <input
          id={`${id}-nome`}
          value={nome}
          maxLength={NOME_MAX_LENGTH}
          autoComplete="off"
          required
          aria-invalid={shown.nome ? true : undefined}
          aria-describedby={shown.nome ? `${id}-nome-erro` : undefined}
          onChange={(event) => setNome(event.target.value)}
        />
        {shown.nome && (
          <p id={`${id}-nome-erro`} className="field-error">
            {shown.nome}
          </p>
        )}
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
