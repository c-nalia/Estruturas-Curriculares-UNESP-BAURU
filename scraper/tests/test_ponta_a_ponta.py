"""Replay das páginas reais (gravadas em 30/09/2026) pelo pipeline inteiro."""
import csv
import io
import json
from dataclasses import replace

import pytest

from curriculos_unesp.coletor import baixador, coletar, cursos_selecionados, salvar
from curriculos_unesp.config import CURSOS, Fonte
from curriculos_unesp.portal import Portal

# pasta -> (tipo e nome esperado de cada item escolhido)
ESPERADO = {
    "FC/DCO/BCC": [("arquivo", "bcc-curriculo-2105-com-quadro-resumo.pdf")],
    "FC/DCO/BSI": [("arquivo", "bsi-curriculo-2804v2.pdf")],
    "FC/DFM/Fisica": [("arquivo", "grade-por-termo-com-ementa-e-objetivo-2.pdf")],
    "FC/DFM/Meteorologia": [("html", "grade-curricular")],
    "FC/DM/Matematica": [("html", "grade-curricular-1507")],
    "FC/DCB/Ciencias_Biologicas": [("arquivo", "curriculo-2710-bacharelado-integral"),
                                   ("arquivo", "curriculo-2711-licenciatura-noturno")],
    "FC/DPSI/Psicologia": [("arquivo", "grade-curricular-curso-de-psicologia-1212-1213.pdf")],
    "FC/DED/Pedagogia": [("arquivo", "matriz-curricular-final---21-12-a-partir-de-2023.pdf")],
    "FC/DEF/Educacao_Fisica": [("arquivo", f"curriculo-{n}---{g}-{t}-a-partir-de-2015.doc")
                               for n, t in (("2611", "noturno"), ("2610", "integral"))
                               for g in ("licenciatura", "bacharelado")],
    "FC/DQ/Quimica": [("arquivo", "2-matrizes-e-ementario-quimica.pdf")],
    "FEB/DEC/Engenharia_Civil": [("arquivo", "ecivil.pdf")],
    "FEB/DEE/Engenharia_Eletrica": [("arquivo", "eeletrica.pdf")],
    "FEB/DEM/Engenharia_Mecanica": [("arquivo", "emecanica.pdf")],
    "FEB/DEP/Engenharia_de_Producao": [("arquivo", "eproducao.pdf")],
    "FAAC/DAUP/Arquitetura_e_Urbanismo": [
        ("html", "matriz-curricular-arquitetura-e-urbanismo"),
        ("arquivo", "estrutura-curricular---arquitetura-e-urbanismo---resolucao-unesp-n-123-de-09-de-novembro-de-2023..pdf")],
    "FAAC/DARG/Artes_Visuais_Bacharelado": [("html", "artes-visuais-estrutura-curricular-basico"),
                                            ("html", "artes-visuais-estrutura-curricular-bacharelado")],
    "FAAC/DARG/Artes_Visuais_Licenciatura": [("html", "artes-visuais-estrutura-curricular-basico"),
                                             ("html", "artes-visuais-estrutura-curricular-licenciatura")],
    "FAAC/DARP/Comunicacao_Audiovisual": [("html", "matriz-curricular-comunicacao-radio-televisao-e-internet")],
    "FAAC/DARP/Relacoes_Publicas": [("html", "matriz-curricular-relacoes-publicas")],
    "FAAC/DDI/Design": [("arquivo", "matriz-curricular-2023-design-unesp.pdf")],
    "FAAC/DJOR/Jornalismo": [("html", "matriz-curricular-jornalismo")],
}


@pytest.fixture
def resultados(replay):
    return {r.curso.pasta: r for r in coletar(CURSOS, replay)}


def test_todos_os_cursos(resultados, replay):
    assert set(resultados) == set(ESPERADO) == {c.pasta for c in CURSOS}
    for pasta, esperado in ESPERADO.items():
        r = resultados[pasta]
        assert r.status == "ok", (pasta, r.detalhe)
        assert [(i.tipo, i.nome) for i in r.itens] == esperado, pasta
    assert not replay.faltando


def test_curriculos_antigos_ficam_registrados(resultados):
    outros = {p: sorted(o["rotulo"] for o in r.outros) for p, r in resultados.items()}
    assert outros["FC/DCO/BCC"] == ["currículo 2102, desde 1995", "currículo 2103, desde 2007", "currículo 2104, desde 2019"]
    assert [o["texto"] for o in resultados["FC/DM/Matematica"].outros] == [
        "1506", "1505 (Em Extinção)", "1504 (Extinto em 2022)", "1503 (Extinto em 2015)"]
    assert all("extin" in o["texto"].lower() for o in resultados["FC/DCB/Ciencias_Biologicas"].outros)
    assert len(resultados["FAAC/DJOR/Jornalismo"].outros) == 2


def test_tabelas_viram_csv(resultados):
    mat = resultados["FC/DM/Matematica"].itens[0]
    linhas = list(csv.reader(io.StringIO(mat.csvs[0])))
    assert linhas[0][:3] == ["Código", "Dep.", "Disciplina"]
    assert any(l[0] == "5100A" and "Funções Elementares" in l for l in linhas)
    jor = resultados["FAAC/DJOR/Jornalismo"].itens[0]
    assert "JOR-E 01 - Jornalismo, Tecnologia e Conhecimento" in jor.csvs[0]
    met = resultados["FC/DFM/Meteorologia"].itens[0]
    assert met.html.count("data:image/png;base64") >= 9  # estrutura em imagens


def test_pagina_inexistente(replay):
    assert Portal("https://www.fc.unesp.br/", replay).pagina("pagina/que-nao-existe/") is None


def test_redescobre_pagina_pelo_menu(replay):
    bcc = next(c for c in CURSOS if c.codigo == "BCC")
    quebrado = replace(bcc, fonte=replace(bcc.fonte, pagina="pagina/que-nao-existe/"))
    [r] = coletar([quebrado], replay)
    assert r.status == "ok" and r.itens[0].nome == "bcc-curriculo-2105-com-quadro-resumo.pdf"


def test_pagina_sumiu_sem_raiz_vira_erro(replay):
    c = replace(CURSOS[0], fonte=Fonte("arquivos", "pagina/que-nao-existe/"), raiz=None)
    [r] = coletar([c], replay)
    assert r.status == "erro" and "não encontrada" in r.detalhe


def test_salvar_estrutura_e_manifesto(resultados, replay, tmp_path):
    lista = list(resultados.values())
    man = salvar(lista, tmp_path, baixador(replay.get_bytes))
    bcc = sorted(p.name for p in (tmp_path / "FC/DCO/BCC").iterdir())
    assert bcc == ["bcc-curriculo-2105-com-quadro-resumo.pdf", "fonte.json"]
    bio = sorted(p.name for p in (tmp_path / "FC/DCB/Ciencias_Biologicas").iterdir())
    assert "curriculo-2710-bacharelado-integral.pdf" in bio  # extensão vem do conteúdo (Drive)
    mat = tmp_path / "FC/DM/Matematica"
    assert (mat / "grade-curricular-1507.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert (mat / "grade-curricular-1507.csv").read_bytes()[:3] == b"\xef\xbb\xbf"  # BOM p/ Excel
    arq = sorted(p.name for p in (tmp_path / "FAAC/DAUP/Arquitetura_e_Urbanismo").iterdir())
    assert "matriz-curricular-arquitetura-e-urbanismo_tabela1.csv" in arq and "matriz-curricular-arquitetura-e-urbanismo_tabela2.csv" in arq
    fonte = json.loads((tmp_path / "FC/DCO/BCC/fonte.json").read_text(encoding="utf-8"))
    assert fonte["estrutura_vigente"][0]["rotulo"] == "currículo 2105, desde 2023"
    assert len(fonte["outros_curriculos_na_pagina"]) == 3
    assert json.loads((tmp_path / "manifesto.json").read_text(encoding="utf-8")) == man
    assert all(c["status"] == "ok" for c in man["cursos"])
    # drive: baixado pelo endpoint de download, não pela página de visualização
    assert any("drive.google.com/uc?export=download&id=" in u for u in replay.baixados)


def test_segunda_execucao_arquiva_o_que_saiu(resultados, replay, tmp_path):
    pasta = tmp_path / "FC/DCO/BCC"
    pasta.mkdir(parents=True)
    (pasta / "bcc_curriculo_2104v2.pdf").write_bytes(b"velho")
    salvar([resultados["FC/DCO/BCC"]], tmp_path, baixador(replay.get_bytes))
    assert (pasta / "_anteriores/bcc_curriculo_2104v2.pdf").read_bytes() == b"velho"


def test_download_que_falha_marca_erro_e_nao_arquiva(resultados, tmp_path):
    pasta = tmp_path / "FC/DCO/BCC"
    pasta.mkdir(parents=True)
    (pasta / "antigo.pdf").write_bytes(b"x")

    def quebra(url):
        raise OSError("sem rede")
    man = salvar([resultados["FC/DCO/BCC"]], tmp_path, quebra)
    assert man["cursos"][0]["status"] == "erro"
    assert (pasta / "antigo.pdf").exists()


def test_cli_listar(replay, tmp_path, monkeypatch, capsys):
    import curriculos_unesp.__main__ as cli
    monkeypatch.setattr(cli, "HttpTransporte", lambda **k: replay)
    assert cli.main(["--so", "FEB", "--listar", "--saida", str(tmp_path)]) == 0
    assert "ecivil.pdf" in capsys.readouterr().out
    assert not any(tmp_path.iterdir())
