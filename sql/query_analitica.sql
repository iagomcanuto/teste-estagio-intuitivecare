
-- QUERY 1: Top 5 operadoras com maior crescimento percentual entre o 1º e o último trimestre (T3)
-- Abordagem: Utilização de Common Table Expressions (CTE) para isolar os períodos.
-- Justificativa Desafio: Filtrei apenas operadoras que possuem dados em ambos os trimestres (T1 e T3) 
-- para garantir uma base de comparação válida, evitando distorções por entrada/saída de operadoras.
WITH q1_2025 AS (
    SELECT cod_operadora, valor_despesa FROM despesas_consolidadas WHERE ano = 2025 AND trimestre = 1
),
q3_2025 AS (
    SELECT cod_operadora, valor_despesa FROM despesas_consolidadas WHERE ano = 2025 AND trimestre = 3
)
SELECT 
    o.razao_social,
    q1.valor_despesa AS valor_inicial,
    q3.valor_despesa AS valor_final,
    ((q3.valor_despesa - q1.valor_despesa) / NULLIF(q1.valor_despesa, 0)) * 100 AS crescimento_percentual
FROM q1_2025 q1
JOIN q3_2025 q3 ON q1.cod_operadora = q3.cod_operadora
JOIN operadoras o ON q1.cod_operadora = o.cod_operadora
WHERE q1.valor_despesa > 0 -- Evita divisão por zero e crescimentos infinitos
ORDER BY crescimento_percentual DESC
LIMIT 5;


-- QUERY 2: Distribuição de despesas por UF e média por operadora (Top 5 Estados)
SELECT 
    o.uf,
    SUM(d.valor_despesa) AS despesa_total,
    COUNT(DISTINCT o.cod_operadora) AS total_operadoras,
    SUM(d.valor_despesa) / COUNT(DISTINCT o.cod_operadora) AS media_por_operadora
FROM despesas_consolidadas d
JOIN operadoras o ON d.cod_operadora = o.cod_operadora
GROUP BY o.uf
ORDER BY despesa_total DESC
LIMIT 5;


-- QUERY 3: Quantas operadoras tiveram despesas acima da média geral em pelo menos 2 dos 3 trimestres?
-- Abordagem: Window Functions ou Subqueries. Escolhi CTEs por legibilidade e facilidade de manutenção.
-- Justificativa Trade-off: Embora o requisito peça o quantitativo
-- optei por uma query que retorna a identificação nominal e o volume financeiro.

WITH medias_gerais AS (
    SELECT ano, trimestre, AVG(valor_despesa) AS media_periodo
    FROM despesas_consolidadas
    GROUP BY ano, trimestre
),
operadoras_acima AS (
    SELECT d.cod_operadora, d.valor_despesa
    FROM despesas_consolidadas d
    JOIN medias_gerais m ON d.ano = m.ano AND d.trimestre = m.trimestre
    WHERE d.valor_despesa > m.media_periodo
)
SELECT 
    o.razao_social, 
    COUNT(*) AS trimestres_acima_da_media,
    SUM(oa.valor_despesa) AS despesa_acumulada_nos_periodos
FROM operadoras_acima oa
JOIN operadoras o ON oa.cod_operadora = o.cod_operadora
GROUP BY o.razao_social
HAVING COUNT(*) >= 2
ORDER BY trimestres_acima_da_media DESC, despesa_acumulada_nos_periodos DESC;

