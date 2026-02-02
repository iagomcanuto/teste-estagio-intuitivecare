# Teste Técnico - Estágio IntuitiveCare 

Este repositório contém a minha solução para o teste de nivelamento da seletiva de estágio da IntuitiveCare. Para este desafio, decidi utilizar o Python; embora eu tenha um conhecimento mais consolidado em Java, escolhi apostar no Python pela abundância de bibliotecas voltadas para análise de dados e aproveitei o desenvolvimento deste projeto para me aprofundar na tecnologia. No banco de dados, utilizei o PostgreSQL 18, que é uma referência no mercado e o SGBD com o qual tive maior contato durante a faculdade, o que me deu segurança para estruturar a modelagem e as queries analíticas pedidas. Para arquitetura optei por usar POO para melhor organização e separação de responsabilidades.

## Tecnologias 

- Python 3
- PostgreSQL 18
- Git

# Decisões Técnicas e Trade-offs

## Teste de integração com API pública

- Estratégia de coleta (1.1)
    A estratégia de coleta usada foi a de busca recursiva, para o código ser resiliente a mudanças nas subpastas e formatos do portal da ANS. Para acessar a API usei a biblioteca requests em conjunto com beautifulsoup. Para lidar com diferentes formatos de arquivos, defini uma variável com os formatos alvo (ZIP, CSV, XLSX) e organizei o retorno das requisições de maneira decrescente para sempre buscar o dado mais recente primeiro. Também implementei um limitador para baixar apenas a quantidade de arquivos necessária, evitando requisições desnecessárias.


- Processamento de arquivos (1.2)
    Para processar os arquivos ZIP, usei a biblioteca zipfile e, para lidar com os dados, a biblioteca pandas. Iniciei validando se os arquivos eram CSV, TXT ou XLSX para evitar erros de leitura. Na filtragem, utilizei o código contábil de despesas com evento/sinistro e implementei uma lógica para manter apenas os registros de "último nível" (que identifiquei como leaf). Como o plano de contas da ANS é hierárquico, essa etapa evita que uma "conta-pai" seja somada junto com seus filhos, o que duplicaria o valor real das despesas. Por fim, normalizei os nomes das colunas e limpei os dados para o padrão de leitura do Python.
       - Trade-off
            Decidi processar os arquivos in-memory (em memória). Como a quantidade de dados brutos é baixa (por volta de 300MB) e, depois de filtrados, o volume se torna ainda menor, não identifiquei necessidade de processamento incremental, levando em consideração o desempenho dos equipamentos atuais.

- Consolidação e Análise de inconsistências (1.3)
    Para a consolidação, utilizei uma lista de DataFrames contendo os dados já normalizados vindos do método filtrar_dados. Concatenei esses trimestres para gerar um arquivo único. Como o arquivo de contabilidade não continha todas as informações necessárias, realizei um merge (join) com o arquivo de cadastro das empresas (CADOP) utilizando o número de registro como chave. O valor das despesas foi obtido calculando a diferença entre os saldos.
       - Trade-off 
         Decidi descartar da planilha empresas que não apresentaram despesas (valores zerados ou negativos). Em casos de razões sociais diferentes para o mesmo CNPJ, optei por manter a primeira razão social encontrada. Para o tratamento de datas, utilizei a biblioteca Pandas para normalização automática; caso alguma data seja inválida ou o processamento falhe, o sistema gera um log de erros contendo esses registros. 

## Teste de transformação e validação de dados

- Validação de dados e estratégias (2.1)
    Para validar os dados, utilizei uma classe específica que identifica registros inválidos e realiza a limpeza. Implementei verificações para validar o CNPJ (conferindo tanto o formato quanto os dígitos verificadores), garantir que os valores fossem positivos e que nenhuma Razão Social estivesse em branco. O código também realiza o tratamento de valores negativos durante a etapa de normalização. 
       - Trade-off
            Para os CNPJs que falharam na validação, optei pela estratégia de descarte com geração de log. Registros inválidos são removidos do processamento principal e salvos em um arquivo de erro separado. 

- Enriquecimento de Dados com Tratamento de Falhas (2.2)
    Utilizando os dados cadastrais previamente obtidos via CADOP, realizei um segundo merge utilizando o CNPJ como chave principal. O objetivo foi enriquecer a base consolidada com informações de Registro ANS, Modalidade e UF.
       - Trade-off
            Para os registros sem "match", optei por mantê-los no arquivo final com as colunas de cadastro vazias (NaN), gerando um log. Essa decisão foi tomada para preservar a integridade financeira, evitando que despesas reais fossem descartadas por inconsistências no cadastro. No caso de CNPJs duplicados com dados divergentes, mantive apenas o primeiro registro encontrado para evitar a duplicação indevida de valores monetários no join. Devido ao baixo volume de dados (inferior a 500MB), escolhi o processamento in-memory pela agilidade e simplicidade na implementação.
            
- Agregação com Múltiplas Estratégias (2.3)
    Nesta etapa final de processamento, utilizei as funções de agrupamento (groupby) do pandas para consolidar os dados por Razão Social e UF. Além do somatório total de despesas por operadora, implementei o cálculo da média trimestral e do desvio padrão, ferramenta estatística essencial para identificar a variabilidade e possíveis anomalias nos gastos reportados.
       - Trade-off
            Escolhi realizar a ordenação dos dados (do maior para o menor valor total) diretamente em memória utilizando o método sort_values do pandas. Como o volume de dados agregados é reduzido, a ordenação in-memory é a estratégia mais eficiente. Não houve necessidade de implementar ordenação externa ou em disco, já que os recursos computacionais disponíveis superam largamente o tamanho do arquivo despesas_agregadas.csv.