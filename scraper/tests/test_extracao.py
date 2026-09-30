import csv
import io

from curriculos_unesp.extracao import (drive_id, html_autonomo, links_arquivos, links_internos,
                                       subpaginas, tabelas_csv, tem_estrutura_embutida, titulo)

BASE = "https://www.fc.unesp.br/"


def test_texto_ao_redor_do_link_traz_o_status():
    html = ('<p><a href="Home/x/2708b.pdf">Currículo: 2708 - Bacharelado</a> (em extinção)<br>'
            '<a href="https://drive.google.com/file/d/1bb5gQDGTUB6Ca6gxT4Ei7y66OKkB1iLA/view">Currículo: 2710</a> (Vigente)</p>')
    a, b = links_arquivos(html, BASE)
    assert a.texto == "Currículo: 2708 - Bacharelado (em extinção)"
    assert a.url == "https://www.fc.unesp.br/Home/x/2708b.pdf"
    assert b.texto.endswith("(Vigente)") and drive_id(b.url) == "1bb5gQDGTUB6Ca6gxT4Ei7y66OKkB1iLA"


def test_dedup_por_url_e_descarta_link_fantasma():
    html = ('<a href="Home/c.doc">- Currículo 2611 - Licenciatura NOTURNO</a> <a href="Home/c.doc">(a partir de 2015);</a>'
            '<a href="Home/fantasma.pdf"></a>')
    [l] = links_arquivos(html, BASE)
    assert "2611" in l.texto and "2015" in l.texto


def test_subpaginas_so_filhos_diretos():
    menu = ('<a href="https://x/#!/cursos/jor/grade-curricular/">Matriz</a>'
            '<a href="https://x/#!/cursos/jor/grade-curricular/ingressantes-a-partir-de-2023/">Ingressantes a partir de 2023</a>'
            '<a href="https://x/#!/cursos/jor/grade-curricular/planos/sub/">neto</a>'
            '<a href="https://x/#!/cursos/jor/outra/">outra</a>')
    [s] = subpaginas(menu, "cursos/jor/grade-curricular/")
    assert s.titulo == "Ingressantes a partir de 2023"


def test_links_internos_antigos():
    html = '<a href="#687,694"><img src="x.png"></a><a href="#687,694">https://www.faac.unesp.br/#687,694</a><a href="#687,695">b</a>'
    assert [(l.id_menu, l.id_item) for l in links_internos(html)] == [("687", "694"), ("687", "695")]


def test_tabela_vira_csv_e_html_autonomo():
    html = ("<h2>Grade Curricular 1507</h2><table><tr><th>Código</th><th>Disciplina</th></tr>"
            "<tr><td>5100A</td><td>Funções Elementares</td></tr><tr><td>5101A</td><td>Matrizes, Cálculo</td></tr></table>")
    assert titulo(html) == "Grade Curricular 1507" and tem_estrutura_embutida(html)
    [c] = tabelas_csv(html)
    assert list(csv.reader(io.StringIO(c)))[2] == ["5101A", "Matrizes, Cálculo"]
    pag = html_autonomo(html, "Grade 1507", "https://www.fc.unesp.br/#!/x/", BASE, "11/Set/2024 16:19")
    assert pag.startswith("<!doctype html>") and '<base href="https://www.fc.unesp.br/">' in pag
    assert "11/Set/2024" in pag and "5100A" in pag


def test_imagem_embutida_conta_como_estrutura():
    assert tem_estrutura_embutida('<p><img src="data:image/png;base64,AAAA"></p>')
    assert not tem_estrutura_embutida('<p>texto</p><table><tr><td>1</td></tr></table>')
