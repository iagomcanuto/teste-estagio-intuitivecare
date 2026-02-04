# Teste Técnico - Estágio IntuitiveCare 

Este repositório contém a minha solução para o teste de nivelamento da seletiva de estágio da IntuitiveCare. Para este desafio, decidi utilizar o Python; embora eu tenha um conhecimento mais consolidado em Java, escolhi apostar no Python pela abundância de bibliotecas voltadas para análise de dados e aproveitei o desenvolvimento deste projeto para me aprofundar na tecnologia. No banco de dados, utilizei o PostgreSQL 18, que é uma referência no mercado e o SGBD com o qual tive maior contato durante a faculdade, o que me deu segurança para estruturar a modelagem e as queries analíticas pedidas. Para arquitetura optei por usar POO para melhor organização e separação de responsabilidades.

## Tecnologias 

- Python 3
- PostgreSQL 18
- Git

## Estrutura de Pastas
    ```
    ├── data/
    │   ├── raw/                        # Arquivos originais baixados da ANS
    │   └── output/                     # CSVs processados e limpos pelo Python
    ├── sql/
    │   ├── stg_query.sql               # Criação das tabelas de staging
    │   ├── query_ddl.sql               # Estrutura final, chaves e índices
    │   ├── query_import.sql            # Scripts de ETL e carga de dados
    │   └── query_analitica.sql         # Consultas de negócio e inteligência
    ├── src/                            # Classes de Scraping e Processamento
    ├── main.py                         # Ponto de entrada da aplicação
    ├── requirements.txt                # Dependências do projeto
    └── README.md                       # Documentação
    ```

## Como Executar
- Prepare o ambiente virtual
```
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
```
- Execute o script para gerar os dados 
```
    python main.py
```
Os arquivos processados serão gerados na pasta /data/output 

Os que nao passaram por processamento (Relatorio_cadop) estarão na pasta /data/raw

- Configure o Banco de Dados

Estrutura: Execute os scripts query_ddl.sql e stg_query.sql no PostgreSQL para criar as tabelas e a área de staging.

Importação: Execute sql/query_import.sql seguindo a ordem: Cadastro de Operadoras primeiro, depois Despesas Consolidadas.

# Decisões Técnicas e Trade-offs

## Teste de integração com API pública

- **Estratégia de coleta (1.1)**

    A estratégia de coleta usada foi a de busca recursiva, para o código ser resiliente a mudanças nas subpastas e formatos do portal da ANS. Para acessar a API usei a biblioteca requests em conjunto com beautifulsoup. Para lidar com diferentes formatos de arquivos, defini uma variável com os formatos alvo (ZIP, CSV, XLSX) e organizei o retorno das requisições de maneira decrescente para sempre buscar o dado mais recente primeiro. Também implementei um limitador para baixar apenas a quantidade de arquivos necessária, evitando requisições desnecessárias.


- **Processamento de arquivos (1.2)**

    Para processar os arquivos ZIP, usei a biblioteca zipfile e, para lidar com os dados, a biblioteca pandas. Iniciei validando se os arquivos eram CSV, TXT ou XLSX para evitar erros de leitura. Na filtragem, utilizei o código contábil de despesas com evento/sinistro e implementei uma lógica para manter apenas os registros de "último nível" (que identifiquei como leaf). Como o plano de contas da ANS é hierárquico, essa etapa evita que uma "conta-pai" seja somada junto com seus filhos, o que duplicaria o valor real das despesas. Por fim, normalizei os nomes das colunas e limpei os dados para o padrão de leitura do Python.

    - **Trade-off**

        Durante o processamento, mantive os valores negativos (estornos e glosas) para garantir a integridade contábil, permitindo que lançamentos errados de entrada fossem devidamente anulados por seus estornos de saída (resolvendo casos de "wash trades"). Decidi processar os arquivos in-memory (em memória). Como a quantidade de dados brutos é baixa (por volta de 300MB) e, depois de filtrados, o volume se torna ainda menor, não identifiquei necessidade de processamento incremental, levando em consideração o desempenho dos equipamentos atuais.

- **Consolidação e Análise de inconsistências (1.3)**

    Para a consolidação, utilizei uma lista de DataFrames contendo os dados já normalizados vindos do método filtrar_dados. Concatenei esses trimestres para gerar um arquivo único. Como o arquivo de contabilidade não continha todas as informações necessárias, realizei um merge (join) com o arquivo de cadastro das empresas (CADOP) utilizando o número de registro como chave. O valor das despesas foi obtido calculando a diferença entre os saldos.

    - **Trade-off**

        Decidi descartar da planilha empresas que não apresentaram despesas (saldos finais zerados ou negativos). Em casos de razões sociais diferentes para o mesmo CNPJ, optei por manter a primeira razão social encontrada. Para o tratamento de datas, utilizei a biblioteca Pandas para normalização automática; caso alguma data seja inválida ou o processamento falhe, o sistema gera um log de erros contendo esses registros. 

## Teste de transformação e validação de dados

- **Validação de dados e estratégias (2.1)**

    Para validar os dados, utilizei uma classe específica que identifica registros inválidos e realiza a limpeza. Implementei verificações para validar o CNPJ (conferindo tanto o formato quanto os dígitos verificadores), garantir que os valores fossem positivos e que nenhuma Razão Social estivesse em branco. O código também realiza o tratamento de valores negativos durante a etapa de consolidação. 

    - **Trade-off**

        Para os CNPJs que falharam na validação, optei pela estratégia de descarte com geração de log. Registros inválidos são removidos do processamento principal e salvos em um arquivo de erro separado. 

- **Enriquecimento de Dados com Tratamento de Falhas (2.2)**

    Utilizando os dados cadastrais previamente obtidos via CADOP, realizei um segundo merge utilizando o CNPJ como chave principal. O objetivo foi enriquecer a base consolidada com informações de Registro ANS, Modalidade e UF.

    - **Trade-off**

        Para os registros sem "match", optei por mantê-los no arquivo final com as colunas de cadastro vazias (NaN), gerando um log. Essa decisão foi tomada para preservar a integridade financeira, evitando que despesas reais fossem descartadas por inconsistências no cadastro. No caso de CNPJs duplicados com dados divergentes, mantive apenas o primeiro registro encontrado para evitar a duplicação indevida de valores monetários no join. Devido ao baixo volume de dados (inferior a 500MB), escolhi o processamento in-memory pela agilidade e simplicidade na implementação.
            
- **Agregação com Múltiplas Estratégias (2.3)**

    Nesta etapa final de processamento, utilizei as funções de agrupamento (groupby) do pandas para consolidar os dados por Razão Social e UF. Além do somatório total de despesas por operadora, implementei o cálculo da média trimestral e do desvio padrão, ferramenta estatística essencial para identificar a variabilidade e possíveis anomalias nos gastos reportados.

    - **Trade-off**

        Escolhi realizar a ordenação dos dados (do maior para o menor valor total) diretamente em memória utilizando o método sort_values do pandas. Como o volume de dados agregados é reduzido, a ordenação in-memory é a estratégia mais eficiente. Não houve necessidade de implementar ordenação externa ou em disco, já que os recursos computacionais disponíveis superam largamente o tamanho do arquivo despesas_agregadas.csv.

## Teste de Banco de Dados e Análise

- **Crie queries DDL para estruturar as tabelas necessárias (3.2)**

    Embora uma arquitetura purista 3NF evitasse a tabela despesas_agregadas (visto que seus dados podem ser derivados), decidi mantê-la e populá-la para atender estritamente aos requisitos do teste técnico e simular uma camada de persistência para relatórios rápidos. Optei por chaves artificiais para desacoplar a integridade do banco de identificadores de negócio. A performance das consultas foi endereçada através de índices estratégicos otimizando o JOIN entre despesas e operadoras, garantindo que o cruzamento de dados permaneça performático com o aumento da base, acelerando filtros temporais (ano/trimestre), evitando a leitura completa da tabela (Full Table Scan) em análises sazonais, e agrupando a filtragem por estado, essencial para a rapidez da análise de distribuição regional.

   - **Trade-off**

        - Normalização (3NF): Optei por tabelas separadas para eliminar redundância e garantir integridade. Atualizações cadastrais refletem instantaneamente no histórico, com JOINs otimizados via chaves numéricas indexadas.
        - Precisão Monetária (DECIMAL): Escolhido pela precisão absoluta. O tipo FLOAT é inadequado para finanças devido a erros de arredondamento binário, e o DECIMAL oferece melhor legibilidade que o armazenamento em centavos (INTEGER).
        -Tipagem de Datas (DATE): Garante a integridade dos dados e permite o uso de funções temporais nativas. O TIMESTAMP foi descartado por ser desnecessário para a granularidade trimestral exigida.

- **Elabore queries para importar o conteúdo dos arquivos CSV (3.3)**

    Adotei a estratégia de Staging Tables, carregando os dados brutos como TEXT para tabelas temporárias. Isso isola falhas de leitura e permite o saneamento dos dados via SQL antes da persistência definitiva.

    - Encoding e Performance: A importação foi realizada via comando \copy com ENCODING 'UTF8'. Garantindo a integridade de caracteres especiais brasileiros.
    Tratamento de Inconsistências:

    - Valores NULL: Utilizei NULLIF(coluna, '') para converter strings vazias em NULL real, evitando erros de tipagem em colunas numéricas e de data.

    - Strings em Campos Numéricos: Implementei validação via Regex (~ '^[0-9.]+$'). Registros com caracteres não numéricos em campos de valor são rejeitados para não comprometer a integridade dos cálculos estatísticos.

    - Datas Inconsistentes: Usei lógica de CASE com Regex para validar o formato ISO. Datas fora do padrão são convertidas em NULL, priorizando a ausência da informação sobre uma data fictícia ou incorreta.

    Minha abordagem foi a de Saneamento Conservador: prefiro rejeitar uma linha com valor financeiro malformado (que distorceria as médias) do que tentar uma conversão que poderia introduzir erros silenciosos no relatório final. Usei ON CONFLICT DO NOTHING para garantir que o processo possa ser rodado várias vezes sem duplicar operadoras.

- **Consultas Analíticas e Inteligência de Dados (3.4)**
    - **Query 1: Quais as 5 operadoras com maior crescimento percentual de despesas entre o primeiro e o último trimestre analisado?**

    Abordagem: Uso de CTEs para isolar as despesas do 1º e do 3º trimestre de 2025.

    Para lidar com dados ausentes Optei por realizar um INNER JOIN entre os períodos. Isso garante que a análise de crescimento seja calculada apenas para operadoras com histórico completo, evitando distorções causadas por entradas ou saídas de empresas no mercado. Usei NULLIF para prevenir erros de divisão por zero.

    | Razão Social | Valor Inicial | Valor Final | Crescimento |
    | :--- | ---: | ---: | ---: |
    | **SAGRADA SAÚDE** | R$ 1.982,37 | R$ 38.366,68 | **1.835,39%** |
    | **UNIMED PARAIBA** | R$ 190,40 | R$ 1.740,03 | **813,88%** |
    | **PORTOMED** | R$ 649.130,14 | R$ 5.854.085,25 | **801,84%** |
    | **SELECT OPERADORA** | R$ 11.171.044,96 | R$ 55.763.817,19 | **399,18%** |
    | **SOCIODONTO** | R$ 5.965,44 | R$ 26.125,52 | **337,95%** |

    - **Query 2: Qual a distribuição de despesas por UF? Liste os 5 estados com maiores despesas totais.**

    Abordagem: Agregação por estado (SUM) associada a um COUNT(DISTINCT cod_operadora).

    | UF | Despesa Total | Operadoras | Média por Operadora |
    | :--- | ---: | ---: | ---: |
    | **SP** | R$ 73.271.916.157,58 | 242 | R$ 302.776.513,05 |
    | **RJ** | R$ 52.407.497.342,21 | 63 | R$ 831.865.037,18 |
    | **MG** | R$ 12.525.152.288,29 | 100 | R$ 125.251.522,88 |
    | **CE** | R$ 12.128.844.004,56 | 16 | R$ 758.052.750,29 |
    | **DF** | R$ 11.173.856.811,20 | 15 | R$ 744.923.787,41 |

    - **Query 3: Quantas operadoras tiveram despesas acima da média geral em pelo menos 2 dos 3 trimestres analisados?**

    Abordagem: Utilização de CTEs modulares para calcular a média global por período e filtrar as ocorrências por operadora.

    Escolhi essa abordagem para priorizar a legibilidade e a manutenibilidade. Embora o requisito peça apenas a quantidade total, a query foi desenhada para retornar a identificação nominal das operadoras. Fornecer os nomes permite a rastreabilidade e conferência manual dos dados, garantindo que a análise seja auditável e transparente

    | Razão Social | Trimestres Acima da Média | Despesa Acumulada |
    | :--- | :---: | ---: |
    | **BRADESCO SAÚDE S.A.** | 3 | R$ 24.132.499.192,47 |
    | **SUL AMÉRICA COMPANHIA DE SEGURO SAÚDE** | 3 | R$ 17.336.442.829,42 |
    | **AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL S.A.** | 3 | R$ 16.418.043.215,48 |
    | **HAPVIDA ASSISTENCIA MEDICA S.A.** | 3 | R$ 7.726.767.218,82 |
    | **NOTRE DAME INTERMÉDICA SAÚDE S.A.** | 3 | R$ 7.707.067.731,38 |

    <details>
    <summary> Clique para expandir a lista completa (89 operadoras)</summary>

    | Razão Social | Trimestres | Despesa Acumulada |
    | :--- | :---: | ---: |
    | CAIXA DE ASSISTÊNCIA DOS FUNCIONÁRIOS DO BANCO DO BRASIL | 3 | R$ 5.894.745.211,22 |
    | UNIMED NACIONAL - COOPERATIVA CENTRAL | 3 | R$ 5.018.895.266,65 |
    | PREVENT SENIOR PRIVATE OPERADORA DE SAÚDE LTDA | 3 | R$ 4.435.266.464,18 |
    | UNIMED BELO HORIZONTE COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 4.274.784.629,47 |
    | PORTO SEGURO - SEGURO SAÚDE S/A | 3 | R$ 4.254.887.864,42 |
    | UNIMED SEGUROS SAÚDE S/A | 3 | R$ 3.953.275.061,79 |
    | UNIMED DO EST. DO RJ FEDERAÇÃO EST. DAS COOPERATIVAS MÉDICAS | 3 | R$ 3.558.208.226,23 |
    | GEAP AUTOGESTÃO EM SAÚDE | 3 | R$ 3.004.107.110,21 |
    | UNIMED PORTO ALEGRE - COOPERATIVA MÉDICA LTDA. | 3 | R$ 2.814.901.842,59 |
    | UNIMED CURITIBA - SOCIEDADE COOPERATIVA DE MÉDICOS | 3 | R$ 2.459.367.408,77 |
    | UNIMED CAMPINAS - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 2.392.848.304,57 |
    | UNIMED DE FORTALEZA SOCIEDADE COOPERATIVA MÉDICA LTDA. | 3 | R$ 1.998.076.603,66 |
    | OMINT SERVIÇOS DE SAÚDE S.A. | 3 | R$ 1.847.451.063,56 |
    | UNIMED GOIANIA COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 1.832.539.764,31 |
    | FUNDAÇÃO SAÚDE ITAÚ | 3 | R$ 1.696.616.125,82 |
    | GRUPO HOSPITALAR DO RIO DE JANEIRO LTDA | 3 | R$ 1.580.487.371,63 |
    | CARE PLUS MEDICINA ASSISTENCIAL LTDA. | 3 | R$ 1.537.758.381,34 |
    | UNIMED VITORIA COOPERATIVA DE TRABALHO MEDICO | 3 | R$ 1.452.171.851,50 |
    | FUNDAÇÃO CESP | 3 | R$ 1.221.339.130,02 |
    | SAMEDIL SERVIÇOS DE ATENDIMENTO MÉDICO S/A | 3 | R$ 1.165.341.933,58 |
    | UNIMED BELÉM COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 1.143.873.444,43 |
    | UNIMED RECIFE COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 1.102.617.232,11 |
    | FUNDAÇÃO ASSISTENCIAL DOS SERVIDORES DO MINISTÉRIO DA FAZENDA | 3 | R$ 1.011.282.161,90 |
    | UNIMED CUIABA COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 990.733.119,52 |
    | UNIMED SAO JOSÉ DO RIO PRETO - COOP. DE TRABALHO MÉDICO | 3 | R$ 975.733.382,30 |
    | UNIMED GRANDE FLORIANÓPOLIS-COOPERATIVA DE TRABALHO MEDICO | 3 | R$ 946.101.204,80 |
    | UNIMED DO ESTADO DE SÃO PAULO - FEDERAÇÃO ESTADUAL DAS COOP. MÉDICAS | 3 | R$ 939.454.146,87 |
    | CAIXA BENEFICENTE DOS FUNCIONARIOS DO BANCO DO ESTADO DE SÃO PAULO | 3 | R$ 895.686.859,50 |
    | UNIMED SOROCABA COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 861.547.310,71 |
    | UNIMED NATAL SOC. COOP. DE TRAB. MÉDICO | 3 | R$ 861.415.109,54 |
    | UNIMED SERRA GAUCHA/RS COOPERATIVA DE ASSISTENCIA A SAUDE LTDA | 3 | R$ 789.323.301,29 |
    | UNIMED DE LONDRINA COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 775.312.426,09 |
    | UNIMED JOAO PESSOA - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 772.608.897,84 |
    | UNIMED MACEIO COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 770.166.586,15 |
    | HUMANA SAÚDE NORDESTE LTDA. | 3 | R$ 760.481.033,62 |
    | UNIMED-SÃO GONÇALO - NITERÓI - SOC.COOP.SERV.MED E HOSP LTDA | 3 | R$ 728.877.833,50 |
    | NOTRE DAME INTERMÉDICA MINAS GERAIS SAÚDE S.A. | 3 | R$ 705.674.906,52 |
    | CAIXA DE ASSISTENCIA DOS SERVIDORES DO ESTADO DE MATO GROSSO DO SUL | 3 | R$ 689.305.593,17 |
    | SANTA HELENA ASSISTÊNCIA MÉDICA S/A. | 3 | R$ 664.960.660,65 |
    | UNIMED DE SANTOS COOP DE TRAB MEDICO | 3 | R$ 651.647.851,25 |
    | UNIMED CAMPO GRANDE MS COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 641.329.832,38 |
    | UNIMED REGIONAL MARINGÁ COOP.DE TRABALHO MÉDICO | 3 | R$ 615.134.564,76 |
    | UNIMED DE RIBEIRAO PRETO - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 610.565.215,13 |
    | CENTRO TRASMONTANO DE SAO PAULO | 3 | R$ 608.362.810,12 |
    | SAMP ESPIRITO SANTO ASSISTENCIA MEDICA SA | 3 | R$ 576.137.338,21 |
    | CLINIPAM CLINICA PARANAENSE DE ASSISTENCIA MEDICA LTDA | 3 | R$ 560.408.124,06 |
    | ODONTOPREV S/A | 3 | R$ 550.547.924,29 |
    | UNIMED BLUMENAU - COOPERATIVA DE TRABALHO MEDICO | 3 | R$ 546.195.072,69 |
    | UNIMED UBERLÂNDIA COOPERATIVA REGIONAL TRABALHO MÉDICO LTDA | 3 | R$ 541.524.671,37 |
    | ASSOCIAÇÃO DE BENEFICÊNCIA E FILANTROPIA SÃO CRISTOVÃO | 3 | R$ 520.471.127,80 |
    | FUNDAÇÃO SÃO FRANCISCO XAVIER | 3 | R$ 515.612.877,35 |
    | UNIMED DO ESTADO DO PARANÁ FEDERAÇÃO ESTADUAL DAS COOPERATIVAS MÉDICAS | 3 | R$ 496.766.249,48 |
    | UNIMED SAO JOSE DOS CAMPOS - COOPERATIVA DE TRABALHO MEDICO | 3 | R$ 495.262.795,42 |
    | UNIMED DE PIRACICABA SOCIEDADE COOPERATIVA DE SERVIÇOS MÉDICOS | 3 | R$ 478.128.723,06 |
    | UNIMED DO ESTADO DE SANTA CATARINA FED. EST. DAS COOP. MÉD. | 3 | R$ 467.750.241,42 |
    | UNIMED DE JOINVILLE COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 448.158.319,86 |
    | UNIMED - COOPERATIVA DE SERVIÇOS DE SAÚDE DOS VALES DO TAQUARI E RIO PARDO LTDA. | 3 | R$ 443.251.658,86 |
    | UNIMED DIVINOPOLIS - COOPERATIVA DE TRABALHO MEDICO LTDA | 3 | R$ 441.182.275,25 |
    | UNIMED TERESINA - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 425.120.243,35 |
    | CEMIG SAÚDE | 3 | R$ 422.340.466,82 |
    | SINDIFISCO NACIONAL | 3 | R$ 413.341.788,48 |
    | UNIMED SERGIPE - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 410.234.203,81 |
    | UNIMED JUIZ DE FORA COOPERATIVA DE TRABALHO MÉDICO LTDA | 3 | R$ 406.504.018,63 |
    | UNIMED LITORAL COOPERATIVA DE TRABALHO MÉDICO LTDA | 3 | R$ 404.052.690,71 |
    | UNIMED DE BAURU COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 397.666.333,85 |
    | UNIMED DE CASCAVEL COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 387.539.323,21 |
    | UNIMED SÃO CARLOS - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 386.360.778,90 |
    | ASSOCIAÇÃO SANTA CASA SAÚDE DE SÃO JOSÉ DOS CAMPOS | 3 | R$ 371.743.765,43 |
    | UNIMED DE PRESIDENTE PRUDENTE COOPERATIVA DE TRAB. MÉDICO | 3 | R$ 361.408.051,06 |
    | PLANO HOSPITAL SAMARITANO LTDA | 3 | R$ 360.798.872,72 |
    | PASA - PLANO DE ASSISTENCIA A SAUDE DO APOSENTADO DA VALE | 3 | R$ 353.538.303,17 |
    | UNIMED JUNDIAI - COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 347.635.099,95 |
    | UNIMED CARUARU-COOPERATIVA DE TRABALHO MEDICO | 3 | R$ 331.316.829,61 |
    | UNIMED DE MACAÉ COOPERATIVA DE ASSISTÊNCIA À SAÚDE | 3 | R$ 329.067.662,69 |
    | UNIMED VALE DO SINOS - COOPERATIVA DE ASSISTÊNCIA À SAÚDE LTDA | 3 | R$ 325.656.874,58 |
    | INSTITUTO CURITIBA DE SAÚDE | 3 | R$ 322.209.839,40 |
    | UNIMED DE VOLTA REDONDA COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 319.917.094,25 |
    | UNIMED NORTE DO MATO GROSSO COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 319.439.946,41 |
    | CAIXA DE ASSISTÊNCIA DOS FUNCIONÁRIOS DO BANCO DO NORDESTE DO BRASIL | 3 | R$ 314.947.309,81 |
    | UNIMED SUL CAPIXABA COOPERATIVA DE TRABALHO MÉDICO | 3 | R$ 311.433.949,12 |
    | CENTRO CLÍNICO GAÚCHO LTDA | 3 | R$ 310.005.755,32 |
    | IPASGO (GO) | 2 | R$ 1.136.962.920,86 |
    | ALICE OPERADORA LTDA. | 2 | R$ 244.724.342,44 |
    | UNIMED NOVA FRIBURGO-SOC.COOP.SERV.MED.HOSP.LTDA. | 2 | R$ 201.077.432,91 |

    </details>

## Teste de API e Interface Web
    
   - **Backend (FastAPI + PostgreSQL)**

Framework: Utilizei o FastAPI pela alta performance e geração automática de documentação OpenAPI (Swagger), o que agiliza o ciclo de desenvolvimento e testes.
    
Paginação: Implementada via Offset-based (limit e page), estratégia ideal para a navegação de dados tabulares da ANS.

Estatísticas: As agregações (Top 5 operadoras, totais e médias) são processadas via Query Direta na View SQL vw_despesas_estatisticas, garantindo que os dados estejam sempre atualizados com o banco.

Estrutura de Resposta: Adotei a Opção B (Dados + Metadados) para facilitar o controle de paginação pelo frontend.

Interface Web (Vue.js)
Devido ao tempo dedicado a garantir a qualidade técnica do processamento dos dados da ANS, a interface Vue.js não foi implementada nesta entrega.

Documentação
A coleção do Postman para teste das rotas está disponível na raiz: IntuitiveCare_API.postman_collection.json.