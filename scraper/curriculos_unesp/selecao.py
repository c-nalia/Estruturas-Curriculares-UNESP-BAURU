"""Decide qual(is) estrutura(s) curricular(es) é(são) a(s) atual(is).

Os sites listam lado a lado currículos novos e antigos, com rótulos livres:
"Currículo 2105 (a partir de 2023)", "Estrutura Curricular (2010-2022)",
"Currículo: 2708 - Bacharelado (em extinção)", "1504 (Extinto em 2022)",
"Ingressantes a partir de 2024", "- Currículo 2611 - Licenciatura NOTURNO"...

Regra:
1. descarta o que está marcado como antigo (extinto, em extinção, "até 2022",
   intervalo "2010-2022") — desde que sobre algo;
2. agrupa por modalidade (bacharelado/licenciatura × integral/noturno/diurno);
3. em cada grupo fica o mais novo por (marcado "vigente", ano de início,
   número do currículo). Sem ano nem número no grupo, fica tudo.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "")
                   if not unicodedata.combining(c)).lower()


_RE_ANTIGO = re.compile(
    r"extint|em extin|\bate\s+(?:o\s+ano\s+de\s+)?(?:19|20)\d\d|\bate\s+\d{1,2}/(?:19|20)\d\d"
    r"|\((?:19|20)\d\d\s*[-–a]\s*(?:19|20)\d\d\)|de\s+(?:19|20)\d\d\s+ate\s+(?:19|20)\d\d")
_RE_VIGENTE = re.compile(r"\bvigente\b(?!\s+ate)")
_RE_ANO = re.compile(
    r"(?:a\s+partir\s+de|ingressantes\s+(?:em|a\s+partir\s+de|desde)|desde|ingressaram\s+a\s+partir\s+de)\s*"
    r"(?:o\s+ano\s+de\s+)?((?:19|20)\d\d)")
_RE_NUM_ROTULADO = re.compile(r"(?:curr[ií]culos?|curriculo|estrutura(?:\s+curricular)?)\s*[:\-–]?\s*(\d{4})\b")
_RE_NUM_SOLTO = re.compile(r"(?<![\d/.-])(\d{4})(?![\d/.-])")


def _eh_ano(n: int) -> bool:
    return 1980 <= n <= 2039


@dataclass
class Rotulo:
    antigo: bool = False
    vigente: bool = False
    ano: Optional[int] = None
    numero: Optional[int] = None
    grau: str = ""      # bacharelado | licenciatura | ""
    turno: str = ""     # integral | noturno | diurno | ""

    @property
    def modalidade(self) -> tuple[str, str]:
        return self.grau, self.turno

    @property
    def chave(self) -> tuple:
        return (self.vigente, self.ano or 0, self.numero or 0)

    def resumo(self) -> str:
        partes = []
        if self.numero:
            partes.append(f"currículo {self.numero}")
        if self.grau or self.turno:
            partes.append(" ".join(p for p in (self.grau, self.turno) if p))
        if self.ano:
            partes.append(f"desde {self.ano}")
        partes.append("antigo" if self.antigo else ("vigente" if self.vigente else ""))
        return ", ".join(p for p in partes if p)


def ler_rotulo(texto: str) -> Rotulo:
    t = sem_acento(texto)
    r = Rotulo()
    r.antigo = bool(_RE_ANTIGO.search(t))
    r.vigente = bool(_RE_VIGENTE.search(t)) and not r.antigo
    anos = [int(a) for a in _RE_ANO.findall(t)]
    r.ano = max(anos) if anos else None
    m = _RE_NUM_ROTULADO.search(t)
    if m and not _eh_ano(int(m.group(1))):
        r.numero = int(m.group(1))
    else:
        soltos = [int(n) for n in _RE_NUM_SOLTO.findall(t) if not _eh_ano(int(n))]
        r.numero = soltos[0] if soltos else None
    if re.search(r"\bbach", t):
        r.grau = "bacharelado"
    elif re.search(r"\blicenc", t):
        r.grau = "licenciatura"
    turnos = [tn for tn in ("integral", "noturno", "diurno") if re.search(rf"\b{tn}\b", t)]  # não "integralização"
    r.turno = turnos[0] if len(turnos) == 1 else ""  # "Integral e Noturno" = vale p/ ambos
    return r


@dataclass
class Candidato(Generic[T]):
    item: T
    texto: str
    rotulo: Rotulo = field(init=False)

    def __post_init__(self):
        self.rotulo = ler_rotulo(self.texto)


def escolher_atuais(cands: list[Candidato[T]]) -> tuple[list[Candidato[T]], list[Candidato[T]]]:
    """Devolve (atuais, preteridos), preservando a ordem da página."""
    if not cands:
        return [], []
    vivos = [c for c in cands if not c.rotulo.antigo] or list(cands)
    grupos: dict[tuple[str, str], list[Candidato[T]]] = {}
    for c in vivos:
        grupos.setdefault(c.rotulo.modalidade, []).append(c)
    # modalidade sem turno/grau (ex. "Bacharelado") não compete com uma mais específica mais nova
    atuais: list[Candidato[T]] = []
    for grupo in grupos.values():
        if not any(c.rotulo.ano or c.rotulo.numero or c.rotulo.vigente for c in grupo):
            atuais.extend(grupo)
            continue
        melhor = max(c.rotulo.chave for c in grupo)
        atuais.extend(c for c in grupo if c.rotulo.chave == melhor)
    ids = {id(c) for c in atuais}
    ordem = [c for c in cands if id(c) in ids]
    return ordem, [c for c in cands if id(c) not in ids]
