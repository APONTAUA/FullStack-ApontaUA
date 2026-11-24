import math

import pytest

from backend.app.modules.reputation.service import (
    calcular_colaboracao,
    calcular_fiabilidade,
    calcular_melhoria_continua,
    calcular_qualidade,
    calcular_reputacao,
    calcular_utilidade,
    detalhar_reputacao,
)


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


@pytest.mark.parametrize(
    ("media", "avaliacoes", "esperado"),
    [
        (0, 0, 50),  # sem avaliações: fica na média de partida
        (5, 1, 54.545),  # uma avaliação quase não desloca
        (1, 1, 45.455),  # um voto mau isolado também não
        (3, 10, 50),  # média a meio da escala
        (5, 10, 75),  # boa média, confiança parcial
        (1, 10, 25),
        (4.6, 50, 83.333),  # muitas avaliações: aproxima-se da média real
    ],
)
def test_qualidade_segue_a_media_bayesiana(media, avaliacoes, esperado):
    """A qualidade considera a média e a quantidade de avaliações (RN-102)."""
    assert calcular_qualidade(media, avaliacoes) == pytest.approx(esperado, abs=0.001)


def test_qualidade_rejeita_media_fora_da_escala():
    """Com avaliações, a média tem de estar entre 1 e 5 estrelas."""
    with pytest.raises(ValueError):
        calcular_qualidade(6, 10)


def test_qualidade_rejeita_numero_negativo_de_avaliacoes():
    """Não existe um número negativo de avaliações."""
    with pytest.raises(ValueError):
        calcular_qualidade(4, -1)


@pytest.mark.parametrize(
    ("consultas", "downloads", "esperado"),
    [(0, 0, 0), (40, 20, 60), (100, 0, 100), (200, 300, 100)],
)
def test_utilidade_sobe_ate_a_referencia(consultas, downloads, esperado):
    """A utilidade considera consultas e downloads válidos (RN-103)."""
    assert calcular_utilidade(consultas, downloads) == pytest.approx(esperado)


@pytest.mark.parametrize(
    ("comentarios", "sugestoes", "esperado"),
    [(0, 0, 0), (3, 1, 20), (10, 10, 100), (50, 0, 100)],
)
def test_colaboracao_sobe_ate_a_referencia(comentarios, sugestoes, esperado):
    """A colaboração considera comentários e sugestões úteis (RN-104)."""
    assert calcular_colaboracao(comentarios, sugestoes) == pytest.approx(esperado)


@pytest.mark.parametrize(("sugestoes", "esperado"), [(0, 0), (2, 20), (10, 100), (25, 100)])
def test_melhoria_continua_sobe_ate_a_referencia(sugestoes, esperado):
    """A melhoria contínua considera sugestões aceites e incorporadas (RN-105)."""
    assert calcular_melhoria_continua(sugestoes) == pytest.approx(esperado)


def test_contagens_negativas_sao_rejeitadas():
    """Nenhum critério aceita contagens negativas."""
    with pytest.raises(ValueError):
        calcular_utilidade(-1, 0)
    with pytest.raises(ValueError):
        calcular_colaboracao(0, -1)
    with pytest.raises(ValueError):
        calcular_melhoria_continua(-1)


@pytest.mark.parametrize(("infracoes", "esperado"), [(0, 100), (1, 75), (4, 0), (6, 0)])
def test_fiabilidade_desce_por_infracao_confirmada(infracoes, esperado):
    """A fiabilidade considera as infrações confirmadas (RN-106)."""
    assert calcular_fiabilidade(infracoes) == pytest.approx(esperado)


def test_fiabilidade_rejeita_numero_negativo_de_infracoes():
    """Não existe um número negativo de infrações."""
    with pytest.raises(ValueError):
        calcular_fiabilidade(-1)


def test_exemplo_completo_do_historial_a_reputacao():
    """Do historial de um utilizador à reputação global, passando pelos cinco critérios."""
    qualidade = calcular_qualidade(media_avaliacoes=4.5, numero_avaliacoes=8)
    utilidade = calcular_utilidade(consultas_validas=40, downloads_validos=20)
    colaboracao = calcular_colaboracao(comentarios_uteis=3, sugestoes_uteis=1)
    melhoria_continua = calcular_melhoria_continua(sugestoes_incorporadas=2)
    fiabilidade = calcular_fiabilidade(infracoes_confirmadas=0)

    reputacao = calcular_reputacao(
        qualidade=qualidade,
        utilidade=utilidade,
        colaboracao=colaboracao,
        melhoria_continua=melhoria_continua,
        fiabilidade=fiabilidade,
    )

    assert reputacao == pytest.approx(54)


NAO_FINITOS = [math.nan, math.inf, -math.inf]


@pytest.mark.parametrize("invalido", NAO_FINITOS)
def test_reputacao_rejeita_valores_nao_finitos(invalido):
    """NaN e infinito não são critérios válidos."""
    with pytest.raises(ValueError):
        calcular_reputacao(
            qualidade=0, utilidade=invalido, colaboracao=0, melhoria_continua=0, fiabilidade=0
        )


@pytest.mark.parametrize("invalido", NAO_FINITOS)
def test_criterios_rejeitam_valores_nao_finitos(invalido):
    """Nenhum critério aceita NaN nem infinito."""
    with pytest.raises(ValueError):
        calcular_qualidade(invalido, 10)
    with pytest.raises(ValueError):
        calcular_qualidade(4, invalido)
    with pytest.raises(ValueError):
        calcular_utilidade(invalido, 0)
    with pytest.raises(ValueError):
        calcular_colaboracao(0, invalido)
    with pytest.raises(ValueError):
        calcular_melhoria_continua(invalido)
    with pytest.raises(ValueError):
        calcular_fiabilidade(invalido)


def test_detalhe_mostra_a_contribuicao_de_cada_criterio():
    """Cada critério contribui com o seu valor vezes o peso (US-053)."""
    detalhe = detalhar_reputacao(
        qualidade=66.667, utilidade=60, colaboracao=20, melhoria_continua=20, fiabilidade=100
    )

    contribuicoes = [criterio.contribuicao for criterio in detalhe.criterios]
    assert contribuicoes == pytest.approx([20, 12, 3, 4, 15], abs=0.001)
    assert detalhe.total == pytest.approx(54, abs=0.001)


def test_detalhe_mantem_a_ordem_dos_criterios():
    """Os critérios aparecem sempre pela mesma ordem, para a interface ser consistente."""
    detalhe = detalhar_reputacao(
        qualidade=0, utilidade=0, colaboracao=0, melhoria_continua=0, fiabilidade=0
    )

    nomes = [criterio.nome for criterio in detalhe.criterios]
    assert nomes == ["qualidade", "utilidade", "colaboracao", "melhoria_continua", "fiabilidade"]


@pytest.mark.parametrize(
    "valores",
    [(0, 0, 0, 0, 0), (100, 100, 100, 100, 100), (80, 50, 40, 60, 100), (13, 77, 5, 91, 42)],
)
def test_soma_das_contribuicoes_e_igual_ao_total(valores):
    """A explicação bate sempre certo com o total (US-053)."""
    q, u, c, m, f = valores
    detalhe = detalhar_reputacao(
        qualidade=q, utilidade=u, colaboracao=c, melhoria_continua=m, fiabilidade=f
    )

    soma = sum(criterio.contribuicao for criterio in detalhe.criterios)
    assert soma == pytest.approx(detalhe.total)


def test_detalhe_rejeita_criterio_fora_da_escala():
    """Os mesmos limites do cálculo global aplicam-se ao detalhe."""
    with pytest.raises(ValueError):
        detalhar_reputacao(
            qualidade=120, utilidade=0, colaboracao=0, melhoria_continua=0, fiabilidade=0
        )
