import pytest

from backend.app.modules.reputation.service import calcular_reputacao


def test_todos_os_criterios_a_zero_devolve_zero():
    """Sem qualquer contribuição, a reputação é 0."""
    result = calcular_reputacao(
        qualidade=0, utilidade=0, colaboracao=0, melhoria_continua=0, fiabilidade=0
    )

    assert result == pytest.approx(0)


def test_todos_os_criterios_no_maximo_devolve_cem():
    """Com todos os critérios no máximo, a reputação é 100 (RN-099)."""
    result = calcular_reputacao(
        qualidade=100, utilidade=100, colaboracao=100, melhoria_continua=100, fiabilidade=100
    )

    assert result == pytest.approx(100)


def test_so_a_qualidade_vale_trinta_por_cento():
    """A qualidade pesa 30% (RN-100)."""
    result = calcular_reputacao(
        qualidade=100, utilidade=0, colaboracao=0, melhoria_continua=0, fiabilidade=0
    )

    assert result == pytest.approx(30)


def test_caso_misto_segue_a_formula_ponderada():
    """Um caso misto segue a fórmula ponderada (RN-101)."""
    result = calcular_reputacao(
        qualidade=80, utilidade=50, colaboracao=40, melhoria_continua=60, fiabilidade=100
    )

    assert result == pytest.approx(67)


def test_criterio_acima_de_cem_e_rejeitado():
    """Um critério fora da escala 0 a 100 é um erro de quem chama."""
    with pytest.raises(ValueError):
        calcular_reputacao(
            qualidade=150, utilidade=0, colaboracao=0, melhoria_continua=0, fiabilidade=0
        )


def test_criterio_negativo_e_rejeitado():
    """Um critério abaixo de 0 também está fora da escala."""
    with pytest.raises(ValueError):
        calcular_reputacao(
            qualidade=50, utilidade=-5, colaboracao=0, melhoria_continua=0, fiabilidade=0
        )
