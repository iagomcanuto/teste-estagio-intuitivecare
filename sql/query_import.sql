
-- Import de dados do CSV para o banco via terminal devido a conflito de permissão 

-- psql -U <USUARIO> -d intuitive_care_db -c "\copy stg_ans FROM '/path/data/output/consolidado_final_limpo.csv' WITH (FORMAT CSV, HEADER, ENCODING 'UTF8', DELIMITER ';')"
-- psql -U <USUARIO> -d intuitive_care_db -c "\copy stg_operadoras  FROM '/path/data/raw/Relatorio_cadop.csv' WITH (FORMAT CSV, HEADER, ENCODING 'UTF8', DELIMITER ';')"
-- psql -U <USUARIO> -d intuitive_care_db -c "\copy stg_agregados  FROM '/path/data/output/despesas_agregadas.csv' WITH (FORMAT CSV, HEADER, ENCODING 'UTF8', DELIMITER ';')"

--    Ordem de execução para garantir integridade: 
--    1. Carga de Operadoras 
--    2. Carga de Despesas 
--    3. Carga de Agregados 


-- 1. POPULAR TABELA: operadoras
-- Tratamento: DISTINCT para evitar duplicatas e CASE para validar formato de data.
INSERT INTO operadoras (
    registro_ans, cnpj, razao_social, modalidade, uf, cidade, data_registro_ans
)
SELECT 
    DISTINCT 
    CAST(NULLIF(registro_ans, '') AS INT),
    cnpj,
    razao_social,
    modalidade,
    uf,
    cidade,
    CASE 
        WHEN data_registro_ans ~ '^\d{4}-\d{2}-\d{2}$' THEN CAST(data_registro_ans AS DATE)
        ELSE NULL 
    END
FROM stg_operadoras
WHERE registro_ans IS NOT NULL 
  AND cnpj IS NOT NULL
ON CONFLICT (registro_ans) DO NOTHING;


-- 2. POPULAR TABELA: despesas_consolidadas
-- Tratamento: 
-- - JOIN com a tabela 'operadoras' para obter a chave artificial 'cod_operadora'.
-- - CAST direto para DECIMAL, pois o CSV original utiliza o ponto como separador decimal.
INSERT INTO despesas_consolidadas (
    cod_operadora, ano, trimestre, valor_despesa
)
SELECT 
    o.cod_operadora,
    CAST(NULLIF(s.ano, '') AS INT),
    CAST(NULLIF(s.trimestre, '') AS INT),
    CAST(s.valor_despesas AS DECIMAL(18,2)) -- Usamos o nome exato 'valor_despesas' da stg_ans
FROM stg_ans s
INNER JOIN operadoras o ON CAST(s.registro_ans AS INT) = o.registro_ans
WHERE s.valor_despesas ~ '^[0-9.]+$' -- Rejeita linhas que não sejam numéricas (com ponto decimal)
  AND s.ano IS NOT NULL;


-- 3. POPULAR TABELA: despesas_agregadas
-- Tratamento: Conversão dos valores agregados do Teste 2.3.
INSERT INTO despesas_agregadas (
    razao_social, uf, valor_total, media_trimestral, desvio_padrao
)
SELECT 
    razao_social,
    uf,
    CAST(total_despesas AS DECIMAL(18,2)),
    CAST(media_trimestral AS DECIMAL(18,2)),
    CAST(desvio_padrao_despesas AS DECIMAL(18,2))
FROM stg_agregados
WHERE razao_social IS NOT NULL;