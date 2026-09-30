"""Regras de vigência com os rótulos reais dos sites (30/09/2026)."""
import pytest

from curriculos_unesp.selecao import Candidato, escolher_atuais, ler_rotulo

CASOS = {
    "BCC": (["Currículo 2102 (a partir de 1995)", "Currículo 2103 (a partir de 2007)",
             "Currículo 2104 (a partir de 2019)", "Currículo 2105 (a partir de 2023)"],
            ["Currículo 2105 (a partir de 2023)"]),
    "BSI": (["Curriculo 2801 (para ingressantes a partir de 1997)", "Curriculo 2802 (para ingressantes a partir de 2007)",
             "Curriculo 2803 (para ingressantes a partir de 2018)*Tempo máximo de integralização",
             "Curriculo 2804 (para ingressantes a partir de 2023)"],
            ["Curriculo 2804 (para ingressantes a partir de 2023)"]),
    "Biologicas": (["Currículo: 2708 - Bacharelado (em extinção)", "Currículo: 2708 - Licenciatura - Integral (em extinção)",
                    "Currículo: 2709 - Licenciatura - Noturno (em extinção)", "Currículo: 2710 - Bacharelado - Integral (Vigente)",
                    "Currículo: 2711 - Licenciatura - Noturno (Vigente)"],
                   ["Currículo: 2710 - Bacharelado - Integral (Vigente)", "Currículo: 2711 - Licenciatura - Noturno (Vigente)"]),
    "Psicologia": (["Currículo 1210/1211, Integral e Noturno (para ingressantes de 2007 até 2022)",
                    "Currículo 1212/1213, Integral e Noturno (para ingressantes a partir de 2023)"],
                   ["Currículo 1212/1213, Integral e Noturno (para ingressantes a partir de 2023)"]),
    "FEB civil": (["Estrutura Curricular (2010-2022)", "Estrutura Curricular vigente (a partir de 2023)"],
                  ["Estrutura Curricular vigente (a partir de 2023)"]),
    "FEB elétrica": (["Estrutura Curricular(Até 2022)", "Estrutura Curricular vigente (a partir de 2023)"],
                     ["Estrutura Curricular vigente (a partir de 2023)"]),
    "Matemática": (["1507", "1506", "1505 (Em Extinção)", "1504 (Extinto em 2022)", "1503 (Extinto em 2015)"], ["1507"]),
    "Jornalismo": (["Ingressantes a partir de 2023", "Ingressantes a partir de 2020", "Ingressantes até 2019"],
                   ["Ingressantes a partir de 2023"]),
    "Design": (["Ingressantes em 2023", "Ingressantes a partir de 2024"], ["Ingressantes a partir de 2024"]),
    "Arquitetura": (["Ingressantes a partir de 2012", "Ingressantes a partir de 2023"], ["Ingressantes a partir de 2023"]),
}


@pytest.mark.parametrize("nome", CASOS)
def test_escolhe_vigente(nome):
    textos, esperado = CASOS[nome]
    atuais, preteridos = escolher_atuais([Candidato(t, t) for t in textos])
    assert [c.texto for c in atuais] == esperado
    assert len(atuais) + len(preteridos) == len(textos)


def test_educacao_fisica_uma_por_modalidade():
    textos = [f"- Currículo {n} - {g} {t} (a partir de {a});"
              for n, a in ((2611, 2015), (2609, 2012)) for g in ("Licenciatura", "Bacharelado") for t in ("NOTURNO",)]
    textos += [f"- Currículo {n} - {g} INTEGRAL (a partir de {a});"
               for n, a in ((2610, 2015), (2608, 2012)) for g in ("Licenciatura", "Bacharelado")]
    textos += ["- Currículo 2607 - Licenciatura Noturno (a partir de 2006);", "- Currículo 2604 - Licenciatura Noturno (a partir de 1999)."]
    atuais, _ = escolher_atuais([Candidato(t, t) for t in textos])
    assert sorted((c.rotulo.numero, c.rotulo.grau, c.rotulo.turno) for c in atuais) == [
        (2610, "bacharelado", "integral"), (2610, "licenciatura", "integral"),
        (2611, "bacharelado", "noturno"), (2611, "licenciatura", "noturno")]


@pytest.mark.parametrize("texto,campos", [
    ("ESTRUTURA CURRICULAR - 1702 BACHARELADO EM METEOROLOGIA", {"numero": 1702, "grau": "bacharelado"}),
    ("Estrutura 2402 Série: 1 - Período: 1", {"numero": 2402}),
    ("Currículo 1212/1213, Integral e Noturno", {"numero": 1212, "turno": ""}),
    ("1504 (Extinto em 2022)", {"numero": 1504, "antigo": True}),
    ("Estrutura Curricular vigente (a partir de 2023)", {"vigente": True, "ano": 2023, "numero": None}),
    ("vigente até 2022", {"vigente": False, "antigo": True}),
])
def test_ler_rotulo(texto, campos):
    r = ler_rotulo(texto)
    for k, v in campos.items():
        assert getattr(r, k) == v, (k, r)


def test_sem_informacao_mantem_tudo():
    atuais, pret = escolher_atuais([Candidato("a", "Matrizes e Ementário"), Candidato("b", "Outro documento")])
    assert len(atuais) == 2 and not pret


def test_se_tudo_e_antigo_fica_o_mais_novo():
    atuais, _ = escolher_atuais([Candidato(t, t) for t in ("Currículo 1503 (extinto)", "Currículo 1504 (em extinção)")])
    assert [c.texto for c in atuais] == ["Currículo 1504 (em extinção)"]
