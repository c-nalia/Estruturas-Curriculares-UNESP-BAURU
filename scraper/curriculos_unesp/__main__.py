"""Uso (de dentro da pasta ``scraper``):
    python -m curriculos_unesp                      # atualiza FEB/, FC/ e FAAC/ na raiz do repositório
    python -m curriculos_unesp --listar             # só mostra o que baixaria
    python -m curriculos_unesp --so FC/DCO FEB      # só alguns cursos
    python -m curriculos_unesp --saida D:/curriculos
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .coletor import baixador, coletar, cursos_selecionados, salvar
from .portal import HttpTransporte


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="curriculos_unesp",
                                 description="Baixa as estruturas curriculares vigentes da FEB, FC e FAAC (UNESP Bauru).")
    pacote = Path(__file__).resolve().parent
    # rodando do repositório (scraper/curriculos_unesp): grava na raiz do repo; instalado via pip: pasta atual
    padrao = pacote.parents[1] if pacote.parent.name == "scraper" else Path.cwd()
    ap.add_argument("--saida", default=str(padrao), help=f"destino das pastas FEB/FC/FAAC (padrão: {padrao})")
    ap.add_argument("--so", nargs="*", help="filtra cursos: FC, FC/DCO, BCC, FEB ...")
    ap.add_argument("--listar", action="store_true", help="só lista, sem baixar")
    ap.add_argument("--pausa", type=float, default=0.5, help="segundos entre requisições")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING, format="%(levelname)s %(message)s")

    t = HttpTransporte(pausa=a.pausa)
    resultados = coletar(cursos_selecionados(a.so), t)
    for r in resultados:
        print(f"[{r.status:13}] {r.curso.pasta}  {r.detalhe}")
        for it in r.itens:
            print(f"      {it.tipo:7} {it.rotulo[:40]:40} {it.nome[:60]}")
    if a.listar:
        return 0
    manifesto = salvar(resultados, Path(a.saida), baixador(t.get_bytes))
    n = sum(len(c["estrutura_vigente"]) for c in manifesto["cursos"])
    print(f"\n{n} item(ns) gravados em {Path(a.saida).resolve()}")
    return 0 if all(r.status == "ok" for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
