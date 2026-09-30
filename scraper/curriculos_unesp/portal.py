"""Cliente do portal institucional da UNESP (sites com URL ``#!/...``).

O portal é uma SPA que carrega o conteúdo via *xajax*: POST na raiz do site
com ``xajax=<função>`` e ``xajaxargs[]=...``. O fluxo para uma página é:

1. ``exibePaginaUrl(<![CDATA[caminho]]>, 'verificaHash')`` -> resposta contém
   ``xajax_exibeMenu(idMenu, idItem, ...)``;
2. ``exibeCorpo(idItem, '', '', '', '')`` -> XML com o HTML da página;
3. ``exibeMenu(idMenu, idItem, ...)`` -> HTML do menu lateral (subpáginas,
   ex.: "Ingressantes a partir de 2023", "1507", "1506 (Em extinção)").

Links antigos do portal no formato ``#<menu>,<item>`` levam direto a
``exibeCorpo(<item>)``.
"""
from __future__ import annotations

import http.cookiejar
import re
import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

import requests

USER_AGENT = (
    "Mozilla/5.0 (compatible; curriculos-unesp-bauru/1.0; +projeto academico)"
)

_RE_MENU = re.compile(r"xajax_exibeMenu\(([^)]*)\)")
_RE_ATUALIZADA = re.compile(r'data-atualizacao-pagina">([^<]+)<')
_RE_CMD = re.compile(
    r'<cmd n="as" t="([^"]+)" p="innerHTML">(.*?)</cmd>', re.DOTALL
)
# Blocos da resposta que não são conteúdo da página
_IGNORAR = {"idTopo", "idMenu", "idCorpoRodape", "pu-breadcrumbs", "pu-wrapper-main-banner"}


class Transporte(Protocol):
    def post(self, url: str, data: list[tuple[str, str]]) -> str: ...
    def get_bytes(self, url: str) -> tuple[bytes, str]: ...


class HttpTransporte:
    """Transporte real via ``requests`` com retry e pausa educada."""

    def __init__(self, pausa: float = 0.5, tentativas: int = 3, timeout: float = 30):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        # O portal guarda estado de navegação na sessão PHP: com cookie, uma
        # 2ª página do mesmo menu volta sem ``xajax_exibeMenu``. Sem cookies
        # cada chamada é independente e sempre traz os ids.
        self.s.cookies.set_policy(http.cookiejar.DefaultCookiePolicy(allowed_domains=[]))
        self.pausa, self.tentativas, self.timeout = pausa, tentativas, timeout

    def _req(self, fn: Callable[[], requests.Response]) -> requests.Response:
        erro: Optional[Exception] = None
        for i in range(self.tentativas):
            try:
                r = fn()
                r.raise_for_status()
                time.sleep(self.pausa)
                return r
            except requests.RequestException as e:  # pragma: no cover - rede
                erro = e
                time.sleep(1.5 * (i + 1))
        raise erro  # type: ignore[misc]

    def post(self, url: str, data: list[tuple[str, str]]) -> str:
        r = self._req(lambda: self.s.post(url, data=data, timeout=self.timeout))
        r.encoding = r.encoding or "utf-8"
        return r.text

    def get_bytes(self, url: str) -> tuple[bytes, str]:
        r = self._req(lambda: self.s.get(url, timeout=self.timeout))
        return r.content, r.headers.get("Content-Type", "")


def _cdata(s: str) -> str:
    return re.sub(r"<!\[CDATA\[|\]\]>", "", s)


def _limpa_arg(a: str) -> str:
    return a.strip().strip("'\"")


@dataclass
class Pagina:
    caminho: str
    id_menu: str
    id_item: str
    html: str        # conteúdo (título + corpo) em ordem de exibição
    menu_html: str = ""
    atualizada: str = ""  # "Atualizada em ..." do rodapé da página


class Portal:
    def __init__(self, base_url: str, transporte: Transporte):
        self.base = base_url if base_url.endswith("/") else base_url + "/"
        self.t = transporte
        self._cache: dict[tuple, str] = {}  # sem cookies o portal é sem estado: dá p/ reaproveitar

    def xajax(self, funcao: str, *args: str) -> str:
        chave = (funcao, args)
        if chave not in self._cache:
            data = [("xajax", funcao), ("xajaxr", str(int(time.time() * 1000)))]
            data += [("xajaxargs[]", a) for a in args]
            self._cache[chave] = self.t.post(self.base, data)
        return self._cache[chave]

    @staticmethod
    def conteudo(resposta_xml: str) -> str:
        """Junta os blocos de conteúdo (título, corpo...) de uma resposta xajax."""
        partes = [
            _cdata(html) for alvo, html in _RE_CMD.findall(resposta_xml)
            if alvo not in _IGNORAR
        ]
        return "\n".join(partes)

    def pagina(self, caminho: str, com_menu: bool = False) -> Optional[Pagina]:
        caminho = caminho.lstrip("/").removeprefix("#!/")
        resp = self.xajax("exibePaginaUrl", f"<![CDATA[{caminho}]]>", "verificaHash")
        m = _RE_MENU.search(resp)
        if not m:
            return None
        args = [_limpa_arg(a) for a in m.group(1).split(",")]
        id_menu, id_item = args[0], args[1]
        if id_item == "1" and caminho.strip("/"):
            # caminho inexistente: o portal cai na página inicial (menu 1, item 1)
            return None
        pag = self.item(id_item, caminho=caminho, id_menu=id_menu)
        if com_menu:
            menu = self.xajax("exibeMenu", *args)
            pag.menu_html = "\n".join(_cdata(h) for alvo, h in _RE_CMD.findall(menu) if alvo == "idMenu")
        return pag

    def item(self, id_item: str, caminho: str = "", id_menu: str = "") -> Pagina:
        """Conteúdo de um item pelo id (usado também por links ``#menu,item``)."""
        corpo = self.xajax("exibeCorpo", id_item, "", "", "", "")
        m = _RE_ATUALIZADA.search(corpo)
        return Pagina(caminho or f"#{id_menu},{id_item}", id_menu, id_item,
                      self.conteudo(corpo), atualizada=m.group(1).strip() if m else "")

    def baixar(self, url: str) -> tuple[bytes, str]:
        return self.t.get_bytes(url)
