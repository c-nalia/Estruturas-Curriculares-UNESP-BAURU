# Verificação das estruturas curriculares: coleta de 30/09/2026

Cada item foi conferido em quatro frentes:

1. **Integridade**: o arquivo abre e tem exatamente o tamanho servido pelo site (PDF/DOC). O HTML foi renderizado
   num navegador e o CSV foi lido de volta.
2. **Identidade**: o documento é do curso da pasta e traz o número do currículo/ano indicado na página. Onde o
   cabeçalho é imagem, a conferência foi visual.
3. **Vigência**: a escolha bate com o rótulo da página ("vigente", "a partir de…", "em extinção", "extinto").
4. **Completude**: todos os termos/séries do curso aparecem.

| Pasta | Item | Conteúdo confere | Vigência na página | Página atualizada | Observações |
|---|---|---|---|---|---|
| FC/DCO/BCC | PDF, 2 págs. | ✅ "Currículo 2105 – para ingressantes a partir de 2023", com quadro-resumo | 2105 é o mais novo (2102/2103/2104 listados) | 29/08/2025 | 2104 (desde 2019) ainda aparece; registrado no `fonte.json` |
| FC/DCO/BSI | PDF, 6 págs. | ✅ cabeçalho (imagem): "2804 - Curso: Bacharelado em Sistemas de Informação" | 2804 "para ingressantes a partir de 2023" | 23/02/2026 | impressão do Sistema de Graduação, com equivalências |
| FC/DFM/Fisica | PDF, 32 págs. | ✅ grade por termo da Licenciatura e do Bacharelado em Física de Materiais, com ementas | página: "Estrutura Curricular 1606" | 24/11/2025 | o PDF não traz o número 1606 no texto; a identificação vem do link |
| FC/DFM/Meteorologia | HTML | ✅ "ESTRUTURA CURRICULAR - 1702 BACHARELADO EM METEOROLOGIA", 3150 h | 1701 marcado "vigente até 2022" | 24/11/2025 | tabelas são **imagens** (9) na página: sem CSV |
| FC/DM/Matematica | HTML + CSV | ✅ "Matriz Curricular … (Currículo 1507 - vigente)", termos 1–8 | 1507 mais novo; 1505 em extinção, 1504/1503 extintos | 11/09/2024 | **1506 também aparece como "vigente"** (turmas anteriores); registrado no `fonte.json` |
| FC/DCB/Ciencias_Biologicas | 2 PDFs (Google Drive) | ✅ grade anual com quadro-resumo e ACEUs; 2710 com 4 anos | 2710 e 2711 "(Vigente)"; 2708/2709 "(em extinção)" | 04/01/2024 | os PDFs não trazem o número no texto; identificação pelo link |
| FC/DPSI/Psicologia | PDF, 6 págs. | ✅ "1212/1213 – Graduação em Psicologia (Integral e Noturno)" | "para ingressantes a partir de 2023"; 1210/1211 "até 2022" | 01/03/2024 | |
| FC/DED/Pedagogia | PDF, 1 pág. | ✅ "Estrutura Curricular do Curso Pedagogia – Proposta de Reestruturação 2023" | "para ingressantes a partir de 2023" | 31/07/2025 | |
| FC/DEF/Educacao_Fisica | 4 DOCs | ✅ cada um é a sua modalidade/turno, "para ingressantes a partir do ano de 2015" | 2610/2611 mais novos (2604–2609 listados) | 10/04/2026 | formato .doc (Word 97) |
| FC/DQ/Quimica | PDF, 21 págs. | ✅ "Matrizes curriculares e ementário… Licenciatura em Química e Bacharelado em Química Tecnológica" | documento único | 03/07/2026 | matrizes em **imagem** (pouco texto extraível) |
| FEB/DEC/Engenharia_Civil | PDF, 6 págs. | ✅ "0104 - Curso: Engenharia Civil", séries 1–5 | "vigente (a partir de 2023)"; anterior "2010-2022" | 07/05/2026 | |
| FEB/DEE/Engenharia_Eletrica | PDF, 6 págs. | ✅ "0304 - Curso: Engenharia Elétrica" | "vigente (a partir de 2023)"; anterior "até 2022" | 02/06/2026 | |
| FEB/DEM/Engenharia_Mecanica | PDF, 6 págs. | ✅ "0204 - Curso: Engenharia Mecânica" | "vigente (a partir de 2023)"; anterior "até 2022" | 02/04/2025 | a página também tem um `estrutura-em-a3.pdf` sem rótulo (ignorado) |
| FEB/DEP/Engenharia_de_Producao | PDF, 5 págs. | ✅ "4403 - Curso: Engenharia de Produção" | "vigente (a partir de 2023)"; anterior "até 2022" | 14/05/2026 | |
| FAAC/DAUP/Arquitetura_e_Urbanismo | HTML + 2 CSV + PDF | ✅ matriz (componentes + disciplinas, 5 anos) e Resolução UNESP 123/2023 | subpágina "Ingressantes a partir de 2023" (outra: 2012) | 27/05/2024 | o texto do PDF sai embaralhado (fontes); conferido visualmente |
| FAAC/DARG/Artes_Visuais_Bacharelado | 2 HTML + 2 CSV | ✅ "Básico 2504" + "Bacharelado 2504B" | única estrutura publicada | 11/11/2025 | o curso tem núcleo básico comum + modalidade a partir do 3º ano |
| FAAC/DARG/Artes_Visuais_Licenciatura | 2 HTML + 2 CSV | ✅ "Básico 2504" + "Licenciatura 2504L" | única estrutura publicada | 11/11/2025 | idem |
| FAAC/DARP/Comunicacao_Audiovisual | HTML + CSV | ✅ "1104I - Curso: Comunicação Audiovisual", séries 1–4 | "Ingressantes a partir de 2023" (única) | 29/07/2026 | |
| FAAC/DARP/Relacoes_Publicas | HTML + CSV | ✅ "Estrutura 2402", séries 1–4 | 2023 (outra: 2015) | 10/02/2023 | |
| FAAC/DDI/Design | PDF, 1 pág. | ✅ "Estrutura Curricular Bacharelado Design · FAAC · UNESP · 2023" | "Ingressantes a partir de 2024" | 13/12/2023 | **ingressantes de 2023 seguem uma matriz de transição** (outro PDF, registrado no `fonte.json`) |
| FAAC/DJOR/Jornalismo | HTML + CSV | ✅ "Estrutura 2205", séries 1–5 (5º ano = 1º semestre) | 2023 (outras: 2020 e "até 2019") | 16/05/2023 | |

**Resultado:** 21 cursos, 28 itens, todos com status `ok` e nenhum trocado entre cursos.

Pontos de atenção:
- **Currículos anteriores ainda ativos.** O repositório traz a estrutura para quem ingressa hoje. Alunos veteranos
  podem estar em outro currículo (ex.: BCC 2104, Matemática 1506, Design "transição 2023"). Todos estão listados em
  `outros_curriculos_na_pagina` no `fonte.json` de cada curso, com link.
- **Estruturas em imagem.** Meteorologia (na página) e Química (no PDF) não têm texto extraível das tabelas. Se o
  projeto precisar dos dados em tabela, vai ser preciso OCR ou digitação.
- **Educação Física** publica em `.doc` (Word 97), não em PDF.
