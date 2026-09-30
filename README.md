# Estruturas curriculares: UNESP Bauru (FEB · FC · FAAC)

**Estrutura curricular vigente** (matriz/grade curricular para quem ingressa hoje) de cada curso de graduação da
Faculdade de Engenharia (FEB), Faculdade de Ciências (FC) e Faculdade de Arquitetura, Artes, Comunicação e Design (FAAC)
do câmpus de Bauru da UNESP. Os arquivos são coletados dos sites oficiais e organizados em `FACULDADE/DEPARTAMENTO/CURSO/`.
O repositório inclui o scraper que mantém tudo atualizado.

> Última coleta: **30/09/2026**. Conferência arquivo por arquivo em [`VERIFICACAO.md`](VERIFICACAO.md).

## Cursos

| Faculdade | Pasta | Curso | Estrutura vigente | Formato |
|---|---|---|---|---|
| FC | [`FC/DCO/BCC`](FC/DCO/BCC) | Ciência da Computação | Currículo 2105 (desde 2023) | PDF |
| FC | [`FC/DCO/BSI`](FC/DCO/BSI) | Sistemas de Informação | Currículo 2804 (desde 2023) | PDF |
| FC | [`FC/DFM/Fisica`](FC/DFM/Fisica) | Física (Lic. e Bach. Física de Materiais) | Currículo 1606 | PDF (grade + ementas) |
| FC | [`FC/DFM/Meteorologia`](FC/DFM/Meteorologia) | Meteorologia | Currículo 1702 | HTML (tabelas em imagem) |
| FC | [`FC/DM/Matematica`](FC/DM/Matematica) | Matemática (Licenciatura) | Currículo 1507 | HTML + CSV |
| FC | [`FC/DCB/Ciencias_Biologicas`](FC/DCB/Ciencias_Biologicas) | Ciências Biológicas | 2710 (Bach. Integral) · 2711 (Lic. Noturno) | PDF ×2 |
| FC | [`FC/DPSI/Psicologia`](FC/DPSI/Psicologia) | Psicologia | Currículo 1212/1213 (desde 2023) | PDF |
| FC | [`FC/DED/Pedagogia`](FC/DED/Pedagogia) | Pedagogia | Matriz desde 2023 | PDF |
| FC | [`FC/DEF/Educacao_Fisica`](FC/DEF/Educacao_Fisica) | Educação Física | 2610 (Integral) · 2611 (Noturno), Lic. e Bach. | DOC ×4 |
| FC | [`FC/DQ/Quimica`](FC/DQ/Quimica) | Química (Lic. e Bach. Tecnológico) | Matrizes e ementário | PDF |
| FEB | [`FEB/DEC/Engenharia_Civil`](FEB/DEC/Engenharia_Civil) | Engenharia Civil | Currículo 0104 (desde 2023) | PDF |
| FEB | [`FEB/DEE/Engenharia_Eletrica`](FEB/DEE/Engenharia_Eletrica) | Engenharia Elétrica | Currículo 0304 (desde 2023) | PDF |
| FEB | [`FEB/DEM/Engenharia_Mecanica`](FEB/DEM/Engenharia_Mecanica) | Engenharia Mecânica | Currículo 0204 (desde 2023) | PDF |
| FEB | [`FEB/DEP/Engenharia_de_Producao`](FEB/DEP/Engenharia_de_Producao) | Engenharia de Produção | Currículo 4403 (desde 2023) | PDF |
| FAAC | [`FAAC/DAUP/Arquitetura_e_Urbanismo`](FAAC/DAUP/Arquitetura_e_Urbanismo) | Arquitetura e Urbanismo | Ingressantes desde 2023 (Res. UNESP 123/2023) | HTML + CSV + PDF |
| FAAC | [`FAAC/DARG/Artes_Visuais_Bacharelado`](FAAC/DARG/Artes_Visuais_Bacharelado) | Artes Visuais: Bacharelado | 2504 Básico + 2504B | HTML + CSV |
| FAAC | [`FAAC/DARG/Artes_Visuais_Licenciatura`](FAAC/DARG/Artes_Visuais_Licenciatura) | Artes Visuais: Licenciatura | 2504 Básico + 2504L | HTML + CSV |
| FAAC | [`FAAC/DARP/Comunicacao_Audiovisual`](FAAC/DARP/Comunicacao_Audiovisual) | Comunicação: Rádio, TV e Internet | Ingressantes desde 2023 (1104) | HTML + CSV |
| FAAC | [`FAAC/DARP/Relacoes_Publicas`](FAAC/DARP/Relacoes_Publicas) | Relações Públicas | Ingressantes desde 2023 (2402) | HTML + CSV |
| FAAC | [`FAAC/DDI/Design`](FAAC/DDI/Design) | Design | Ingressantes desde 2024 | PDF |
| FAAC | [`FAAC/DJOR/Jornalismo`](FAAC/DJOR/Jornalismo) | Jornalismo | Ingressantes desde 2023 (2205) | HTML + CSV |

### O que tem em cada pasta de curso
- **PDF/DOC**: o documento oficial publicado pelo curso.
- **`.html`**: quando a estrutura é uma tabela na própria página do site, uma cópia autônoma da página (abre no navegador,
  mantém imagens embutidas, com link para a fonte).
- **`.csv`**: as tabelas dessas páginas em formato de planilha (UTF-8 com BOM: abre direto no Excel).
- **`fonte.json`**: página de origem, data de atualização da página e o currículo escolhido. Inclui também os
  **outros currículos listados na página** (ex.: BCC 2104, Matemática 1506), com status, para quem precisar
  de alunos em currículos anteriores.

[`manifesto.json`](manifesto.json) junta tudo isso para uso programático.

### Como o "vigente" é escolhido
Dos currículos listados na página, ficam só os marcados como vigentes ou os mais novos ("a partir de 2023",
"Ingressantes a partir de 2024", maior número de currículo), um por modalidade (bacharelado/licenciatura ×
integral/noturno). Os marcados "em extinção", "extinto", "até 2022" ou "2010-2022" são descartados.
Não entram PPP, planos de ensino nem tabelas de equivalência.

## Atualizar

**Automático:** o workflow [`atualizar-estruturas`](.github/workflows/atualizar-estruturas.yml) roda toda segunda-feira
(e sob demanda na aba *Actions*) e faz commit só quando algo muda. Se uma página sumir ou mudar de formato,
a execução falha e o GitHub avisa por e-mail.

**Local:**
```bash
cd scraper
pip install -r requirements.txt
python -m curriculos_unesp            # atualiza FEB/, FC/ e FAAC/ na raiz do repositório
python -m curriculos_unesp --listar   # só mostra o que baixaria
```
Detalhes técnicos, manutenção e testes: [`scraper/README.md`](scraper/README.md).

## Aviso
As estruturas curriculares são documentos públicos da UNESP. A fonte oficial é sempre a página indicada no
`fonte.json` de cada curso. A licença deste repositório ([MIT](LICENSE)) cobre apenas o código.
