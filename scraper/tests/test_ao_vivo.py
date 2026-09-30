"""Teste contra o site real. Só roda com UNESP_AO_VIVO=1."""
import os

import pytest

from curriculos_unesp.coletor import baixador, coletar
from curriculos_unesp.config import CURSOS
from curriculos_unesp.portal import HttpTransporte

pytestmark = pytest.mark.skipif(os.environ.get("UNESP_AO_VIVO") != "1",
                                reason="defina UNESP_AO_VIVO=1 para testar no site real")


def test_site_real():
    t = HttpTransporte(pausa=0.3)
    res = coletar(CURSOS, t)
    problemas = [f"{r.curso.pasta}: {r.status} {r.detalhe}" for r in res if r.status != "ok"]
    assert not problemas, "\n".join(problemas)
    baixar = baixador(t.get_bytes)
    for r in res:
        for it in r.itens:
            if it.tipo == "arquivo":
                assert len(baixar(it.url)) > 1000, it.url
