"""Orquestra: para cada curso, encontra a estrutura curricular vigente e grava."""
from __future__ import annotations

import json
import logging
import re
import zipfile
import io
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import CURSOS, SITES, Curso
from .extracao import (Link, drive_id, html_autonomo, links_arquivos, links_internos,
                       subpaginas, tabelas_csv, tem_estrutura_embutida, texto_pagina, titulo)
from .portal import Pagina, Portal, Transporte
from .selecao import Candidato, escolher_atuais, ler_rotulo, sem_acento

log = logging.getLogger("curriculos_unesp")
_RE_MENU_ESTRUTURA = re.compile(r"estrutura|grade curricular|matriz")


@dataclass
class Item:
    tipo: str                 # arquivo | html
    nome: str                 # nome do arquivo de saída (sem extensão para html)
    url: str                  # arquivo: URL p/ baixar; html: página de origem
    texto: str
    rotulo: str
    html: Optional[str] = None
    csvs: list[str] = field(default_factory=list)
    atualizada: str = ""


@dataclass
class Resultado:
    curso: Curso
    status: str = "ok"                # ok | sem_estrutura | erro
    detalhe: str = ""
    pagina_url: Optional[str] = None
    atualizada: str = ""
    itens: list[Item] = field(default_factory=list)
    outros: list[dict] = field(default_factory=list)   # currículos listados mas não escolhidos
    salvos: list[str] = field(default_factory=list)


def slug(s: str, n: int = 80) -> str:
    return re.sub(r"[^a-z0-9]+", "-", sem_acento(s)).strip("-")[:n].strip("-") or "estrutura"


def _filtra(textos_itens, incluir: Optional[str], excluir: Optional[str]):
    out = []
    for texto, it in textos_itens:
        t = sem_acento(texto)
        if incluir and not re.search(incluir, t):
            continue
        if excluir and re.search(excluir, t):
            continue
        out.append((texto, it))
    return out


def _outros(preteridos: list[Candidato], url_de) -> list[dict]:
    return [{"texto": c.texto, "rotulo": c.rotulo.resumo(), "url": url_de(c.item)} for c in preteridos]


def _item_html(portal: Portal, pag: Pagina, texto: str, rotulo: str, url: str) -> Item:
    tit = titulo(pag.html) or texto
    if not rotulo:  # ex. "ESTRUTURA CURRICULAR - 1702 BACHARELADO EM METEOROLOGIA" no corpo
        cabecalho = texto_pagina(pag.html)[:200].split("(")[0]  # sem observações entre parênteses
        rotulo = ler_rotulo(cabecalho).resumo()
    return Item("html", slug(tit), url, texto or tit, rotulo,
                html=html_autonomo(pag.html, tit, url, portal.base, pag.atualizada),
                csvs=tabelas_csv(pag.html), atualizada=pag.atualizada)


def _pagina(portal: Portal, curso: Curso, caminho: str, com_menu: bool = False) -> Optional[Pagina]:
    pag = portal.pagina(caminho, com_menu=com_menu)
    if pag or not curso.raiz:
        return pag
    raiz = portal.pagina(curso.raiz, com_menu=True)
    if raiz:
        for a in BeautifulSoup(raiz.menu_html, "html.parser").find_all("a", href=True):
            if _RE_MENU_ESTRUTURA.search(sem_acento(a.get_text())) and "#!/" in a["href"]:
                novo = a["href"].split("#!/", 1)[1]
                log.warning("%s: página mudou; usando %s", curso.pasta, novo)
                return portal.pagina(novo, com_menu=com_menu)
    return None


def _coletar_curso(portal: Portal, curso: Curso, r: Resultado) -> None:
    f = curso.fonte
    pag = _pagina(portal, curso, f.pagina, com_menu=(f.modo == "subpaginas"))
    if pag is None:
        r.status, r.detalhe = "erro", f"página não encontrada: #!/{f.pagina}"
        return
    r.pagina_url, r.atualizada = f"{portal.base}#!/{pag.caminho}", pag.atualizada

    if f.modo == "arquivos":
        links = _filtra([(l.texto, l) for l in links_arquivos(pag.html, portal.base)], f.incluir, f.excluir)
        atuais, pret = escolher_atuais([Candidato(l, t) for t, l in links])
        for c in atuais:
            l: Link = c.item
            nome = l.nome_arquivo if not drive_id(l.url) else slug(l.texto_link)
            r.itens.append(Item("arquivo", nome, l.url, l.texto, c.rotulo.resumo(), atualizada=pag.atualizada))
        r.outros = _outros(pret, lambda l: l.url)

    elif f.modo == "pagina":
        if tem_estrutura_embutida(pag.html):
            r.itens.append(_item_html(portal, pag, "", "", r.pagina_url))

    elif f.modo == "subpaginas":
        subs = _filtra([(s.titulo, s) for s in subpaginas(pag.menu_html, f.grupo or f.pagina)],
                       f.incluir, f.excluir)
        atuais, pret = escolher_atuais([Candidato(s, t) for t, s in subs])
        r.outros = _outros(pret, lambda s: f"{portal.base}#!/{s.caminho}")
        for c in atuais:
            sp = portal.pagina(c.item.caminho)
            if sp is None:
                continue
            url = f"{portal.base}#!/{sp.caminho}"
            r.pagina_url, r.atualizada = url, sp.atualizada
            if tem_estrutura_embutida(sp.html):
                r.itens.append(_item_html(portal, sp, c.texto, c.rotulo.resumo(), url))
            if f.arquivos_incluir:
                for t, l in _filtra([(l.texto, l) for l in links_arquivos(sp.html, portal.base)],
                                    f.arquivos_incluir, None):
                    r.itens.append(Item("arquivo", l.nome_arquivo, l.url, t, c.rotulo.resumo(),
                                        atualizada=sp.atualizada))

    elif f.modo == "internos":
        for li in links_internos(pag.html):
            it = portal.item(li.id_item, id_menu=li.id_menu)
            tit = titulo(it.html)
            if f.incluir and not re.search(f.incluir, sem_acento(tit)):
                continue
            r.itens.append(_item_html(portal, it, tit, "", f"{portal.base}#{li.id_menu},{li.id_item}"))
    else:  # pragma: no cover
        raise ValueError(f"modo desconhecido: {f.modo}")

    if not r.itens:
        r.status, r.detalhe = "sem_estrutura", "página encontrada, mas sem estrutura curricular identificável"


def coletar(cursos: Iterable[Curso], transporte: Transporte) -> list[Resultado]:
    """Fase 1: identifica o que baixar (só lê páginas)."""
    portais: dict[str, Portal] = {}
    saida = []
    for curso in cursos:
        r = Resultado(curso)
        saida.append(r)
        portal = portais.setdefault(curso.faculdade, Portal(SITES[curso.faculdade], transporte))
        try:
            _coletar_curso(portal, curso, r)
        except Exception as e:  # noqa: BLE001 - um curso não derruba os outros
            log.exception("falha em %s", curso.pasta)
            r.status, r.detalhe = "erro", repr(e)
    return saida


# ------------------------------------------------------------------ download ---
def _extensao(dados: bytes) -> str:
    if dados[:4] == b"%PDF":
        return ".pdf"
    if dados[:4] == b"\xd0\xcf\x11\xe0":
        return ".doc"
    if dados[:2] == b"PK":
        try:
            nomes = zipfile.ZipFile(io.BytesIO(dados)).namelist()
            return ".docx" if any(n.startswith("word/") for n in nomes) else \
                   ".xlsx" if any(n.startswith("xl/") for n in nomes) else ".zip"
        except zipfile.BadZipFile:
            return ".bin"
    if dados[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if dados[:3] == b"\xff\xd8\xff":
        return ".jpg"
    return ".bin"


def baixador(get_bytes: Callable[[str], tuple[bytes, str]]) -> Callable[[str], bytes]:
    """Baixa URLs comuns e do Google Drive (inclusive a tela de confirmação)."""
    def baixar(url: str) -> bytes:
        did = drive_id(url)
        if did:
            url = f"https://drive.google.com/uc?export=download&id={did}"
        dados, tipo = get_bytes(url)
        if did and ("text/html" in tipo or dados.lstrip()[:15].lower().startswith((b"<!doctype", b"<html"))):
            s = BeautifulSoup(dados, "html.parser")
            form = s.find("form", id="download-form") or s.find("form")
            if form is None:
                raise RuntimeError("Google Drive não liberou o download (arquivo privado?)")
            params = "&".join(f"{i['name']}={i.get('value', '')}" for i in form.find_all("input", attrs={"name": True}))
            dados, tipo = get_bytes(urljoin(url, form.get("action", "")) + "?" + params)
        if dados.lstrip()[:15].lower().startswith((b"<!doctype", b"<html")):
            raise RuntimeError(f"esperava um arquivo e veio HTML: {url}")
        return dados
    return baixar


# ------------------------------------------------------------------- gravação ---
_MANTER = {"fonte.json"}


def _arquivar_antigos(pasta: Path, atuais: set[str]) -> None:
    """Move para ``_anteriores/`` o que sobrou de execuções passadas (nunca apaga)."""
    antigos = [p for p in pasta.iterdir() if p.is_file() and p.name not in atuais | _MANTER]
    if not antigos:
        return
    dest = pasta / "_anteriores"
    dest.mkdir(exist_ok=True)
    for p in antigos:
        alvo = dest / p.name
        if alvo.exists():
            alvo = dest / f"{p.stem}_{datetime.now():%Y%m%d%H%M%S}{p.suffix}"
        p.replace(alvo)


def _unico(nome: str, usados: set[str]) -> str:
    base, ext = (nome.rsplit(".", 1) + [""])[:2] if "." in nome else (nome, "")
    final, i = nome, 2
    while final.lower() in usados:
        final = f"{base}_{i}" + (f".{ext}" if ext else "")
        i += 1
    usados.add(final.lower())
    return final


def salvar(resultados: list[Resultado], destino: Path, baixar: Callable[[str], bytes]) -> dict:
    """Fase 2: baixa/grava em destino/FACULDADE/DEPTO/CURSO + fonte.json + manifesto.json."""
    manifesto = {"gerado_em": datetime.now().isoformat(timespec="seconds"), "cursos": []}
    for r in resultados:
        pasta = destino / r.curso.pasta
        pasta.mkdir(parents=True, exist_ok=True)
        usados: set[str] = set()
        registros, falhas = [], 0
        for it in r.itens:
            reg = {"tipo": it.tipo, "texto": it.texto, "rotulo": it.rotulo,
                   "origem": it.url, "pagina_atualizada_em": it.atualizada}
            try:
                if it.tipo == "arquivo":
                    dados = baixar(it.url)
                    nome = it.nome if "." in it.nome[-6:] else it.nome + _extensao(dados)
                    nome = _unico(re.sub(r'[<>:"/\\|?*]+', "_", nome), usados)
                    (pasta / nome).write_bytes(dados)
                    reg.update(arquivo=nome, bytes=len(dados))
                    r.salvos.append(nome)
                else:
                    nome = _unico(it.nome + ".html", usados)
                    (pasta / nome).write_text(it.html or "", encoding="utf-8")
                    reg.update(arquivo=nome, csv=[])
                    r.salvos.append(nome)
                    for i, c in enumerate(it.csvs, 1):
                        cn = _unico(f"{it.nome}.csv" if len(it.csvs) == 1 else f"{it.nome}_tabela{i}.csv", usados)
                        (pasta / cn).write_text(c, encoding="utf-8-sig")  # BOM: Excel abre com acentos certos
                        reg["csv"].append(cn)
                        r.salvos.append(cn)
            except Exception as e:  # noqa: BLE001
                falhas += 1
                log.error("%s: falha em %s: %r", r.curso.pasta, it.url[:120], e)
                reg["erro"] = repr(e)
            registros.append(reg)
        if r.status == "ok" and falhas:
            r.status, r.detalhe = "erro", f"{falhas} arquivo(s) não baixado(s)"
        if r.status == "ok":
            _arquivar_antigos(pasta, set(r.salvos))
        entrada = {"faculdade": r.curso.faculdade, "departamento": r.curso.departamento,
                   "curso": r.curso.codigo, "nome": r.curso.nome, "pasta": r.curso.pasta,
                   "pagina": r.pagina_url, "pagina_atualizada_em": r.atualizada,
                   "status": r.status, "detalhe": r.detalhe,
                   "estrutura_vigente": registros, "outros_curriculos_na_pagina": r.outros}
        (pasta / "fonte.json").write_text(json.dumps(entrada, ensure_ascii=False, indent=2), encoding="utf-8")
        manifesto["cursos"].append(entrada)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def cursos_selecionados(filtro: Optional[list[str]]) -> list[Curso]:
    if not filtro:
        return list(CURSOS)
    f = [x.upper().strip("/") for x in filtro]
    return [c for c in CURSOS if any(c.pasta.upper().startswith(x) or c.codigo.upper() == x for x in f)]
