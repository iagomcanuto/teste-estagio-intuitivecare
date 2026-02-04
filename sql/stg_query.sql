
--  Staging para Dados Cadastrais (Relatorio_cadop.csv)
CREATE TABLE stg_operadoras (
    registro_ans TEXT,
    cnpj TEXT,
    razao_social TEXT,
    nome_fantasia TEXT,
    modalidade TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    cep TEXT,
    ddd TEXT,
    telefone TEXT,
    fax TEXT,
    email TEXT,
    representante TEXT,
    cargo_representante TEXT,
    regiao_comercializacao TEXT,
    data_registro_ans TEXT
);

--  Staging para Dados Financeiros Consolidados (consolidado_final_limpo.csv)
CREATE TABLE stg_ans (
    cnpj TEXT,
    razao_social TEXT,
    trimestre TEXT,
    ano TEXT,
    valor_despesas TEXT,
    registro_ans TEXT,
    modalidade TEXT,
    uf TEXT
);

--  Staging para Dados Agregados (despesas_agregadas.csv do teste 2.3)
CREATE TABLE stg_agregados (
    razao_social TEXT,
    uf TEXT,
    total_despesas TEXT,
    media_trimestral TEXT,
    desvio_padrao_despesas TEXT
);

-- Comentário técnico: As tabelas acima aceitam qualquer formato de string. 
-- O tratamento de pontos, vírgulas e datas é feito via SQL no script query_import.sql.