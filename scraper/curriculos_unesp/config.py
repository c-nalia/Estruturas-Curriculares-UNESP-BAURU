"""Onde cada curso de graduação da FEB, FC e FAAC (UNESP Bauru) publica a
estrutura curricular, e como ler cada página.

Modos de coleta (``Fonte.modo``):

``arquivos``   a página lista PDFs/DOCs de vários currículos: filtra os links
               por ``incluir``/``excluir`` e fica com o(s) vigente(s).
``pagina``     a estrutura é a própria página (tabela/imagens): salva HTML+CSV.
``subpaginas`` a estrutura fica em subpáginas do menu ("Ingressantes a partir
               de 2023", "1507", "1506 (Em extinção)"): escolhe a vigente e salva
               HTML+CSV (e os arquivos dela, se ``arquivos_incluir``).
``internos``   a página aponta para itens por links antigos ``#menu,item``
               (Artes Visuais: Básico / Bacharelado / Licenciatura): salva todos
               os que casam com ``incluir``.

Regex são aplicadas ao texto sem acento e em minúsculas.
Caminhos são o que vem depois de ``#!/`` na URL do site.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SITES = {
    "FC": "https://www.fc.unesp.br/",
    "FEB": "https://www.feb.unesp.br/",
    "FAAC": "https://www.faac.unesp.br/",
}


@dataclass(frozen=True)
class Fonte:
    modo: str                          # arquivos | pagina | subpaginas | internos
    pagina: str
    grupo: Optional[str] = None        # subpaginas: prefixo dos itens do menu
    incluir: Optional[str] = None
    excluir: Optional[str] = None
    arquivos_incluir: Optional[str] = None  # subpaginas: arquivos a baixar da subpágina escolhida


@dataclass(frozen=True)
class Curso:
    faculdade: str
    departamento: str
    codigo: str
    nome: str
    fonte: Fonte
    raiz: Optional[str] = None   # página do curso: se ``fonte.pagina`` sumir, procura no menu

    @property
    def base_url(self) -> str:
        return SITES[self.faculdade]

    @property
    def pasta(self) -> str:
        return f"{self.faculdade}/{self.departamento}/{self.codigo}"


_FC_DCO = "departamentos/computacao/cursos-de-graduao/"
_FEB = "graduacao/secao-de-graduacao/cursos-de-graduacao/"
_FAAC = "graduacao/cursos/"


def _feb(depto: str, codigo: str, nome: str, slug: str) -> Curso:
    return Curso("FEB", depto, codigo, nome,
                 Fonte("arquivos", _FEB + slug + "/", incluir=r"estrutura curricular"))


def _faac_sub(depto: str, codigo: str, nome: str, slug: str, arquivos: Optional[str] = None) -> Curso:
    return Curso("FAAC", depto, codigo, nome,
                 Fonte("subpaginas", _FAAC + slug + "/", grupo=_FAAC + slug + "/grade-curricular/",
                       incluir=r"ingressantes", excluir=r"^ac\b|aacc|atividades|planos|solicita",
                       arquivos_incluir=arquivos))


CURSOS: list[Curso] = [
    # ---------------- FC - Faculdade de Ciências ----------------
    Curso("FC", "DCO", "BCC", "Bacharelado em Ciência da Computação",
          Fonte("arquivos", _FC_DCO + "bacharelado-em-ciencia-da-computacao/estrutura-curricular/", incluir=r"curriculo"),
          raiz=_FC_DCO + "bacharelado-em-ciencia-da-computacao/"),
    Curso("FC", "DCO", "BSI", "Bacharelado em Sistemas de Informação",
          Fonte("arquivos", _FC_DCO + "bacharelado-em-sistemas-de-informacao/grade-curricular/", incluir=r"curriculo"),
          raiz=_FC_DCO + "bacharelado-em-sistemas-de-informacao/"),
    Curso("FC", "DFM", "Fisica", "Física (Licenciatura e Bacharelado em Física de Materiais)",
          Fonte("arquivos", "departamentos/fisica/cursos/fsica/grade-curricular/", incluir=r"^estrutura curricular"),
          raiz="departamentos/fisica/cursos/fsica/apresentacaoteste/"),
    Curso("FC", "DFM", "Meteorologia", "Bacharelado em Meteorologia",
          Fonte("pagina", "departamentos/fisica/cursos/meteorologia/grade-curricular/"),
          raiz="departamentos/fisica/cursos/meteorologia/"),
    Curso("FC", "DM", "Matematica", "Licenciatura em Matemática",
          Fonte("subpaginas", "departamentos/matematica/graduacao/",
                grupo="departamentos/matematica/graduacao/grade-curricular/")),
    Curso("FC", "DCB", "Ciencias_Biologicas", "Ciências Biológicas (Bacharelado e Licenciatura)",
          Fonte("arquivos", "departamentos/ciencias-biologicas/coordenacao-do-curso/grade-curricular/", incluir=r"curriculo"),
          raiz="departamentos/ciencias-biologicas/"),
    Curso("FC", "DPSI", "Psicologia", "Psicologia (Integral e Noturno)",
          Fonte("arquivos", "departamentos/psicologia/curso-de-psicologia/documentos-do-curso/", incluir=r"^curriculo")),
    Curso("FC", "DED", "Pedagogia", "Licenciatura em Pedagogia",
          Fonte("arquivos", "cursos/pedagogia/grade-curricular/", incluir=r"matriz"),
          raiz="cursos/pedagogia/"),
    Curso("FC", "DEF", "Educacao_Fisica", "Educação Física (Bacharelado e Licenciatura)",
          Fonte("arquivos", "departamentos/dep-educacao-fisica/cursos/grade-curricular/", incluir=r"curriculo"),
          raiz="departamentos/dep-educacao-fisica/"),
    Curso("FC", "DQ", "Quimica", "Química (Licenciatura e Bacharelado Tecnológico)",
          Fonte("arquivos", "departamentos/quimica/coordenacao-de-curso/dados-do-curso/", incluir=r"matriz")),

    # ---------------- FEB - Faculdade de Engenharia ----------------
    _feb("DEC", "Engenharia_Civil", "Engenharia Civil", "engenharia-civil"),
    _feb("DEE", "Engenharia_Eletrica", "Engenharia Elétrica", "engenharia-eletrica"),
    _feb("DEM", "Engenharia_Mecanica", "Engenharia Mecânica", "engenharia-mecanica"),
    _feb("DEP", "Engenharia_de_Producao", "Engenharia de Produção", "engenharia-de-producao"),

    # ---------------- FAAC ----------------
    _faac_sub("DAUP", "Arquitetura_e_Urbanismo", "Arquitetura e Urbanismo", "arquitetura-e-urbanismo",
              arquivos=r"estrutura|resolu"),
    Curso("FAAC", "DARG", "Artes_Visuais_Bacharelado", "Artes Visuais - Bacharelado (Básico + Bacharelado)",
          Fonte("internos", _FAAC + "artes-visuais/grade-curricular/", incluir=r"basico|bacharelado")),
    Curso("FAAC", "DARG", "Artes_Visuais_Licenciatura", "Artes Visuais - Licenciatura (Básico + Licenciatura)",
          Fonte("internos", _FAAC + "artes-visuais/grade-curricular/", incluir=r"basico|licenciatura")),
    _faac_sub("DARP", "Comunicacao_Audiovisual", "Comunicação: Rádio, TV e Internet (Audiovisual)", "radialismo"),
    _faac_sub("DARP", "Relacoes_Publicas", "Relações Públicas", "relacoes-publicas"),
    Curso("FAAC", "DDI", "Design", "Design",
          Fonte("arquivos", _FAAC + "design/grade-curricular/", incluir=r"ingressantes")),
    _faac_sub("DJOR", "Jornalismo", "Jornalismo", "jornalismo"),
]
