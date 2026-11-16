"""Cálculo da reputação dos utilizadores (US-051)."""

PESO_QUALIDADE = 30 / 100
PESO_UTILIDADE = 20 / 100
PESO_COLABORACAO = 15 / 100
PESO_MELHORIA_CONTINUA = 20 / 100
PESO_FIABILIDADE = 15 / 100


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
