

--  Tabela de Operadoras
CREATE TABLE operadoras (
    cod_operadora INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    registro_ans INT UNIQUE NOT NULL,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100), -- Dimensão importante para análise
    uf CHAR(2) NOT NULL,
    cidade VARCHAR(100),
    data_registro_ans DATE
);

--  Tabela de Despesas 
CREATE TABLE despesas_consolidadas (
    cod_despesa INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_operadora INT NOT NULL,
    ano INT NOT NULL,
    trimestre INT NOT NULL,
    valor_despesa DECIMAL(18, 2) NOT NULL,
    CONSTRAINT fk_operadora FOREIGN KEY (cod_operadora) REFERENCES operadoras(cod_operadora)
);

--  Tabela de Agregados (Requisito do teste 3.2 para importação do CSV 2.3)
CREATE TABLE despesas_agregadas (
    cod_agregado INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    razao_social VARCHAR(255),
    uf CHAR(2),
    valor_total DECIMAL(18, 2),
    media_trimestral DECIMAL(18, 2),
    desvio_padrao DECIMAL(18, 2)
);

--  View de Estatísticas (Abordagem Purista 3NF)
CREATE OR REPLACE VIEW vw_despesas_estatisticas AS
SELECT 
    o.razao_social AS "RazaoSocial",
    o.uf AS "UF",
    SUM(d.valor_despesa) AS "Total_Despesas",
    AVG(d.valor_despesa) AS "Media_Trimestral",
    STDDEV(d.valor_despesa) AS "Desvio_Padrao_Despesas"
FROM despesas_consolidadas d
JOIN operadoras o ON d.cod_operadora = o.cod_operadora
GROUP BY o.cod_operadora, o.razao_social, o.uf;

--  Índices de Performance
CREATE INDEX idx_despesas_cod_operadora ON despesas_consolidadas(cod_operadora);
CREATE INDEX idx_despesas_periodo ON despesas_consolidadas(ano, trimestre);
CREATE INDEX idx_operadoras_uf ON operadoras(uf);