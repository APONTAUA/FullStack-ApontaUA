"""Cálculo da reputação dos utilizadores (US-051)."""

# Valores iniciais, a recalibrar com os dados do piloto (ver docs/reputation/formulas.md).
ESTRELAS_MINIMO = 1
ESTRELAS_MAXIMO = 5
MEDIA_DE_PARTIDA = 3.0
PESO_DA_MEDIA_DE_PARTIDA = 10

INTERACOES_DE_REFERENCIA = 100
CONTRIBUICOES_DE_REFERENCIA = 20
SUGESTOES_DE_REFERENCIA = 10

PESO_QUALIDADE = 30 / 100
PESO_UTILIDADE = 20 / 100
PESO_COLABORACAO = 15 / 100
PESO_MELHORIA_CONTINUA = 20 / 100
PESO_FIABILIDADE = 15 / 100

PENALIZACAO_POR_INFRACAO = 25


def calcular_reputacao(
    qualidade: float,
    utilidade: float,
    colaboracao: float,
    melhoria_continua: float,
    fiabilidade: float,
) -> float:
    """Calcula a reputação global (0 a 100) a partir dos cinco critérios (RN-101)."""
    pesos = [
        PESO_QUALIDADE,
        PESO_UTILIDADE,
        PESO_COLABORACAO,
        PESO_MELHORIA_CONTINUA,
        PESO_FIABILIDADE,
    ]
    criterios = [qualidade, utilidade, colaboracao, melhoria_continua, fiabilidade]
    reputacao = 0

    if any(n > 100 or n < 0 for n in criterios):
        raise ValueError("Cada critério de reputação tem de estar entre 0 e 100.")

    for i in range(0, len(pesos)):
        reputacao = reputacao + (pesos[i] * criterios[i])

    return reputacao


def calcular_qualidade(media_avaliacoes: float, numero_avaliacoes: int) -> float:
    """Calcula a qualidade (0 a 100) pela média bayesiana das avaliações (RN-102)."""
    if numero_avaliacoes < 0:
        raise ValueError("O número de avaliações não pode ser negativo.")

    if numero_avaliacoes > 0 and (
        media_avaliacoes < ESTRELAS_MINIMO or media_avaliacoes > ESTRELAS_MAXIMO
    ):
        raise ValueError("A média das avaliações tem de estar entre 1 e 5 estrelas.")

    media_ajustada = (
        numero_avaliacoes * media_avaliacoes + PESO_DA_MEDIA_DE_PARTIDA * MEDIA_DE_PARTIDA
    ) / (numero_avaliacoes + PESO_DA_MEDIA_DE_PARTIDA)

    return (media_ajustada - ESTRELAS_MINIMO) / (ESTRELAS_MAXIMO - ESTRELAS_MINIMO) * 100


def _normalizar(valor: float, referencia: float) -> float:
    """Normalização linear com teto: 0 dá 0, a referência (ou mais) dá 100."""
    if valor < 0:
        raise ValueError("O valor a normalizar não pode ser negativo.")
    return min(valor / referencia, 1) * 100


def calcular_utilidade(consultas_validas: int, downloads_validos: int) -> float:
    """Calcula a utilidade (0 a 100) a partir das consultas e downloads válidos (RN-103)."""
    if consultas_validas < 0 or downloads_validos < 0:
        raise ValueError("As contagens não podem ser negativas.")
    return _normalizar(consultas_validas + downloads_validos, INTERACOES_DE_REFERENCIA)


def calcular_colaboracao(comentarios_uteis: int, sugestoes_uteis: int) -> float:
    """Calcula a colaboração (0 a 100) a partir das contribuições úteis (RN-104)."""
    if comentarios_uteis < 0 or sugestoes_uteis < 0:
        raise ValueError("As contagens não podem ser negativas.")
    return _normalizar(comentarios_uteis + sugestoes_uteis, CONTRIBUICOES_DE_REFERENCIA)


def calcular_melhoria_continua(sugestoes_incorporadas: int) -> float:
    """Calcula a melhoria contínua (0 a 100) a partir das sugestões incorporadas (RN-105)."""
    return _normalizar(sugestoes_incorporadas, SUGESTOES_DE_REFERENCIA)


def calcular_fiabilidade(infracoes_confirmadas: int) -> float:
    """Calcula a fiabilidade (0 a 100): começa em 100 e desce por infração confirmada (RN-106)."""
    if infracoes_confirmadas < 0:
        raise ValueError("O número de infrações não pode ser negativo.")
    return max(100 - PENALIZACAO_POR_INFRACAO * infracoes_confirmadas, 0)
