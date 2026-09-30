"""Extrai de uma página do portal: links para arquivos (com o texto ao redor),
subpáginas do menu, links antigos ``#menu,item`` e tabelas (HTML/CSV)."""
from __future__ import annotations

import csv
import html as htmlmod
import io
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

EXTENSOES = (".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".ods", ".png", ".jpg", ".jpeg")
_BLOCOS = {"p", "div", "li", "tr", "td", "th", "br", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol"}
_RE_DRIVE = re.compile(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:[^#]*&)?id=)([\w-]{10,})")


def _sopa(html: str) -> BeautifulSoup:
    s = BeautifulSoup(html, "html.parser")
    for lixo in s(["script", "style"]):
        lixo.decompose()
    return s


def _txt(s: str) -> str:
    return " ".join((s or "").split())


def drive_id(url: str) -> Optional[str]:
    m = _RE_DRIVE.search(url)
    return m.group(1) if m else None


def eh_arquivo(href: str) -> bool:
    h = href.lower().split("?")[0].split("#")[0]
    return h.endswith(EXTENSOES) or drive_id(href) is not None


@dataclass
class Link:
    url: str
    texto: str          # texto do link + o que vem logo depois na mesma linha
    texto_link: str

    @property
    def nome_arquivo(self) -> str:
        did = drive_id(self.url)
        if did:
            return f"drive_{did}.pdf"
        return unquote(urlparse(self.url).path.rsplit("/", 1)[-1])


def _texto_depois(a: Tag, limite: int = 120) -> str:
    """Texto que segue o link até a próxima quebra de linha/bloco ou outro link."""
    partes, n = [], 0
    for irmao in a.next_siblings:
        if isinstance(irmao, Tag) and (irmao.name in _BLOCOS or irmao.name == "a" or irmao.find("a")):
            break
        t = irmao.get_text(" ") if isinstance(irmao, Tag) else str(irmao)
        partes.append(t)
        n += len(t)
        if n > limite:
            break
    return _txt(" ".join(partes))[:limite]


def links_arquivos(html: str, base_url: str) -> list[Link]:
    """Links para arquivos, deduplicados por URL (juntando os textos).

    Links sem texto nenhum são restos invisíveis de versões antigas e só
    entram se a mesma URL também aparecer com texto.
    """
    por_url: dict[str, Link] = {}
    for a in _sopa(html).find_all("a", href=True):
        href = a["href"].strip()
        if not eh_arquivo(href):
            continue
        url = urljoin(base_url, href)
        tl = _txt(a.get_text(" "))
        texto = _txt(f"{tl} {_texto_depois(a)}")
        if url in por_url:
            ant = por_url[url]
            if texto and texto not in ant.texto:
                ant.texto = _txt(f"{ant.texto} {texto}")
                ant.texto_link = ant.texto_link or tl
        else:
            por_url[url] = Link(url, texto, tl)
    return [l for l in por_url.values() if l.texto_link]


@dataclass
class Subpagina:
    caminho: str
    titulo: str


def subpaginas(menu_html: str, grupo: str) -> list[Subpagina]:
    """Itens do menu logo abaixo de ``grupo`` (ex.: .../grade-curricular/)."""
    grupo = grupo.strip("/") + "/"
    vistos, saida = set(), []
    for a in _sopa(menu_html).find_all("a", href=True):
        href = a["href"]
        if "#!/" not in href:
            continue
        cam = href.split("#!/", 1)[1]
        resto = cam[len(grupo):] if cam.startswith(grupo) else None
        if not resto or not resto.strip("/") or "/" in resto.strip("/"):
            continue
        if cam in vistos:
            continue
        vistos.add(cam)
        saida.append(Subpagina(cam, _txt(a.get_text(" "))))
    return saida


@dataclass
class LinkInterno:
    id_menu: str
    id_item: str
    texto: str


def links_internos(html: str) -> list[LinkInterno]:
    """Links no formato antigo ``#687,694`` (menu, item)."""
    saida, vistos = [], set()
    for a in _sopa(html).find_all("a", href=True):
        m = re.search(r"#(\d+),(\d+)$", a["href"].strip())
        if m and m.group(2) not in vistos:
            vistos.add(m.group(2))
            saida.append(LinkInterno(m.group(1), m.group(2), _txt(a.get_text(" "))))
    return saida


def titulo(html: str) -> str:
    s = _sopa(html)
    for tag in ("h1", "h2", "h3"):
        h = s.find(tag)
        if h and _txt(h.get_text(" ")):
            return _txt(h.get_text(" "))
    return _txt(s.get_text(" "))[:80]


def texto_pagina(html: str) -> str:
    return _txt(_sopa(html).get_text(" "))


def tem_estrutura_embutida(html: str) -> bool:
    """A página tem a estrutura na própria página (tabela ou imagem embutida)?"""
    s = _sopa(html)
    if any(len(t.find_all("tr")) >= 3 for t in s.find_all("table")):
        return True
    return any(str(i.get("src", "")).startswith("data:image") for i in s.find_all("img"))


def tabelas_csv(html: str) -> list[str]:
    """Cada <table> com pelo menos 3 linhas vira um CSV (texto das células)."""
    saida = []
    for tab in _sopa(html).find_all("table"):
        linhas = []
        for tr in tab.find_all("tr"):
            if tr.find_parent("table") is not tab:
                continue  # tabela aninhada: vira CSV próprio
            celulas = [_txt(c.get_text(" ")) for c in tr.find_all(["td", "th"], recursive=False)]
            if any(celulas):
                linhas.append(celulas)
        if len(linhas) >= 3:
            buf = io.StringIO()
            csv.writer(buf, lineterminator="\n").writerows(linhas)
            saida.append(buf.getvalue())
    return saida


def html_autonomo(corpo: str, titulo_pag: str, url_origem: str, base_url: str, atualizada: str = "") -> str:
    """Página HTML que abre sozinha (imagens embutidas preservadas, links relativos ao site)."""
    s = _sopa(corpo)
    for lixo in s.select("script, style, .fa-info-circle"):
        lixo.decompose()
    t = htmlmod.escape(titulo_pag)
    nota = f"Fonte: <a href=\"{htmlmod.escape(url_origem)}\">{htmlmod.escape(url_origem)}</a>"
    if atualizada:
        nota += f" · página atualizada em {htmlmod.escape(atualizada)}"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="{htmlmod.escape(base_url)}">
<title>{t}</title>
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;margin:12px 0;font-size:14px}} td,th{{border:1px solid #bbb;padding:4px 8px;vertical-align:top}}
img{{max-width:100%;height:auto}} .fonte{{font-size:13px;color:#555;border-bottom:1px solid #ddd;padding-bottom:8px}}
</style></head><body>
<p class="fonte">{nota}</p>
{s}
</body></html>
"""
