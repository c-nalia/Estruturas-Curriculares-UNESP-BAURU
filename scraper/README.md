# scraper: `curriculos_unesp`

Coleta a estrutura curricular vigente de cada curso da FEB, FC e FAAC (UNESP Bauru) e grava em
`FACULDADE/DEPTO/CURSO/` na raiz do repositório.

```bash
pip install -r requirements.txt           # ou: pip install -e ".[dev]"
python -m curriculos_unesp                 # atualiza ../FEB, ../FC, ../FAAC e ../manifesto.json
python -m curriculos_unesp --listar        # só mostra o que baixaria
python -m curriculos_unesp --so FC/DCO FEB # só alguns cursos (pasta, faculdade ou código: BCC)
python -m curriculos_unesp --saida /outro/lugar
```
Arquivos que saíram de uso numa nova coleta vão para `_anteriores/` na pasta do curso (ignorada pelo git).
Nada é apagado.

## Como funciona

### O portal
Os sites (`www.fc|feb|faac.unesp.br/#!/...`) são SPAs que carregam o conteúdo via **xajax**: POST na raiz
com `xajax=<função>&xajaxargs[]=...`. O scraper chama as mesmas funções que o navegador:

| Chamada | Retorno |
|---|---|
| `exibePaginaUrl(<![CDATA[caminho]]>, 'verificaHash')` | `xajax_exibeMenu(idMenu, idItem, …)`; `idItem == 1` = página inexistente (o portal cai na home) |
| `exibeCorpo(idItem, '', '', '', '')` | XML com o HTML da página e a data "Atualizada em" |
| `exibeMenu(idMenu, idItem, …)` | menu lateral (subpáginas, ex.: "Ingressantes a partir de 2023", "1507") |

Links antigos no formato `#<menu>,<item>` (usados em Artes Visuais) vão direto para `exibeCorpo(<item>)`.
O portal guarda estado na sessão PHP: com cookie, a 2ª página do mesmo menu volta sem os ids. Por isso o cliente
roda **sem cookies** (e, sem estado, as respostas podem ser cacheadas durante a execução).

### Modos de coleta (`config.py`)
| Modo | Quando | Exemplos |
|---|---|---|
| `arquivos` | a página lista PDFs/DOCs de vários currículos | BCC, BSI, Biológicas, Ed. Física, FEB, Design |
| `pagina` | a estrutura é a própria página | Meteorologia |
| `subpaginas` | cada currículo é uma subpágina do menu | Matemática, Arquitetura, Jornalismo, RP, Com. Audiovisual |
| `internos` | a página aponta itens por `#menu,item` | Artes Visuais (Básico / Bacharelado / Licenciatura) |

### Escolha do vigente (`selecao.py`)
Cada candidato (texto do link **mais o que vem logo depois dele na mesma linha**, onde costuma estar
"(em extinção)") vira um rótulo com: antigo?, vigente?, ano de início, número do currículo e modalidade
(bacharelado/licenciatura × integral/noturno/diurno). O algoritmo:
1. descarta os antigos (extinto, em extinção, "até 2022", "2010-2022"), desde que sobre algum;
2. agrupa por modalidade;
3. em cada grupo fica o maior (vigente, ano, número). Sem nenhuma informação, fica tudo.

Os preteridos vão para `outros_curriculos_na_pagina` no `fonte.json`.

### Saída
- arquivos com o nome original. Os do Google Drive recebem o nome do link, com a extensão detectada pelo conteúdo;
- páginas: `.html` autônomo (com `<base>` para os links do site e as imagens embutidas preservadas) + `.csv`
  por tabela (UTF-8 com BOM);
- `fonte.json` por curso e `manifesto.json` na raiz.

Downloads do Google Drive usam `uc?export=download&id=…`, inclusive passando pela tela de confirmação de
arquivos grandes. Se vier HTML no lugar de um arquivo, é tratado como erro.

## Módulos
| Arquivo | Papel |
|---|---|
| `config.py` | **tudo que é específico de curso**: página, modo, filtros, siglas das pastas |
| `portal.py` | cliente xajax + transporte HTTP (retry, pausa, sem cookies) |
| `extracao.py` | links com contexto, subpáginas, links `#menu,item`, HTML autônomo, CSV |
| `selecao.py` | leitura dos rótulos e escolha do currículo vigente |
| `coletor.py` | orquestração, download (inclui Drive), gravação, arquivamento |

Siglas conferidas nos sites: **DCO, DFM, DJOR, DAUP**. As demais seguem o padrão usual e podem ser trocadas no
`config.py` (só mudam o nome da pasta).

## Testes
```bash
python -m pytest -q                                       # offline: respostas reais gravadas em 30/09/2026
UNESP_AO_VIVO=1 python -m pytest tests/test_ao_vivo.py    # contra os sites reais
```
- `test_selecao.py`: regras de vigência com os rótulos reais de cada curso;
- `test_extracao.py`: links com contexto, subpáginas, links internos, CSV, HTML;
- `test_baixador.py`: Google Drive (direto e com confirmação), detecção de extensão;
- `test_ponta_a_ponta.py`: pipeline inteiro nos 21 cursos com *replay* das respostas xajax reais
  (`tests/fixtures/*.json`), página inexistente, redescoberta pelo menu, gravação, arquivamento e CLI.

Para regravar as fixtures depois de uma mudança no site, repita as chamadas da tabela acima e salve
`{"site": ..., "calls": [{"fn", "args", "resp"}]}`. O `ReplayTransporte` de `tests/conftest.py` lista em
`faltando` as chamadas que ainda não estão gravadas.
