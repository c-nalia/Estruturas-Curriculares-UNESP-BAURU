import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FIX = Path(__file__).parent / "fixtures"


class Faltando(KeyError):
    pass


class ReplayTransporte:
    """Responde as chamadas xajax com respostas reais gravadas do site.

    Downloads devolvem um PDF falso (o conteúdo não importa nos testes) e
    ficam registrados em ``baixados``. Chamadas não gravadas vão para
    ``faltando`` (útil para regravar as fixtures).
    """

    def __init__(self, pasta: Path = FIX):
        self.gravadas: dict = {}
        for f in sorted(pasta.glob("*.json")):
            obj = json.loads(f.read_text(encoding="utf-8"))
            host = urlparse(obj["site"]).netloc
            for c in obj["calls"]:
                self.gravadas[(host, c["fn"], tuple(c["args"]))] = c["resp"]
        self.baixados: list[str] = []
        self.faltando: list[tuple] = []

    def post(self, url, data):
        fn = next(v for k, v in data if k == "xajax")
        args = tuple(v for k, v in data if k == "xajaxargs[]")
        chave = (urlparse(url).netloc, fn, args)
        if chave not in self.gravadas:
            self.faltando.append(chave)
            raise Faltando(chave)
        return self.gravadas[chave]

    def get_bytes(self, url):
        self.baixados.append(url)
        return b"%PDF-1.4 falso " + url.encode(), "application/pdf"


@pytest.fixture
def replay():
    return ReplayTransporte()
