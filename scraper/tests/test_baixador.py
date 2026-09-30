import pytest

from curriculos_unesp.coletor import _extensao, baixador

PDF = b"%PDF-1.7 conteudo"


def test_drive_direto():
    pedidos = []

    def get(url):
        pedidos.append(url)
        return PDF, "application/pdf"
    assert baixador(get)("https://drive.google.com/file/d/ABCDEFGHIJKL123/view") == PDF
    assert pedidos == ["https://drive.google.com/uc?export=download&id=ABCDEFGHIJKL123"]


def test_drive_com_tela_de_confirmacao():
    aviso = (b'<!DOCTYPE html><html><form id="download-form" action="https://drive.usercontent.google.com/download">'
             b'<input type="hidden" name="id" value="ABCDEFGHIJKL123"><input type="hidden" name="confirm" value="t">'
             b'</form></html>')
    respostas = iter([(aviso, "text/html"), (PDF, "application/pdf")])
    pedidos = []

    def get(url):
        pedidos.append(url)
        return next(respostas)
    assert baixador(get)("https://drive.google.com/file/d/ABCDEFGHIJKL123/view?usp=sharing") == PDF
    assert pedidos[1] == "https://drive.usercontent.google.com/download?id=ABCDEFGHIJKL123&confirm=t"


def test_html_no_lugar_do_arquivo_e_erro():
    with pytest.raises(RuntimeError):
        baixador(lambda u: (b"<html>erro 404</html>", "text/html"))("https://www.fc.unesp.br/Home/x.pdf")


@pytest.mark.parametrize("dados,ext", [
    (b"%PDF-1.4", ".pdf"), (b"\xd0\xcf\x11\xe0....", ".doc"), (b"\x89PNG\r\n\x1a\n..", ".png"), (b"??", ".bin")])
def test_extensao_pelo_conteudo(dados, ext):
    assert _extensao(dados) == ext
