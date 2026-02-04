from fastapi import FastAPI, HTTPException
import pandas as pd
from sqlalchemy import create_engine

app = FastAPI(title="API IntuitiveCare - Iago Canuto")

# --- CONEXÃO COM O SEU POSTGRES ---
# Substitua 'SENHA' e 'BANCO' pelos respectivos dados 
DATABASE_URL = "postgresql://postgres:[SENHA]@localhost:5432/[BANCO]"
engine = create_engine(DATABASE_URL)

@app.get("/api/operadoras")
def listar_operadoras(page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    # Usando a tabela 'operadoras' do seu DDL
    query = f"SELECT * FROM operadoras ORDER BY cod_operadora LIMIT {limit} OFFSET {offset}"
    df = pd.read_sql(query, engine)
    total = pd.read_sql("SELECT COUNT(*) FROM operadoras", engine).iloc[0, 0]
    
    return {
        "data": df.to_dict(orient="records"),
        "total": int(total),
        "page": page,
        "limit": limit
    }

@app.get("/api/operadoras/{cnpj}")
def buscar_por_cnpj(cnpj: str):
    query = f"SELECT * FROM operadoras WHERE cnpj = '{cnpj}'"
    df = pd.read_sql(query, engine)
    if df.empty:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return df.to_dict(orient="records")[0]

@app.get("/api/operadoras/{cnpj}/despesas")
def historico_despesas(cnpj: str):
    # Join entre 'operadoras' e 'despesas_consolidadas' conforme seu esquema
    query = f"""
        SELECT d.* FROM despesas_consolidadas d
        JOIN operadoras o ON d.cod_operadora = o.cod_operadora
        WHERE o.cnpj = '{cnpj}'
        ORDER BY d.ano DESC, d.trimestre DESC
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")

@app.get("/api/estatisticas")
def obter_estatisticas():
    # Usando a VIEW para simplificar a API
    query_top5 = 'SELECT * FROM vw_despesas_estatisticas ORDER BY "Total_Despesas" DESC LIMIT 5'
    df_top5 = pd.read_sql(query_top5, engine)
    return {
        "top_5_operadoras": df_top5.to_dict(orient="records")
    }