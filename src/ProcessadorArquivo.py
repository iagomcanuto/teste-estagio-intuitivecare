import pandas
import os
import zipfile

class ProcessadorArquivo:
    def __init__(self, saida, entrada):
        self.saida = saida 
        self.entrada = entrada
        self.dados_consolidados = []
        
    def abrir_arquivo(self):
        for root, dirs, files in os.walk(self.entrada):
            nome_arquivo:str
            for nome_arquivo in files:
                if nome_arquivo.lower().endswith((".csv", ".txt", ".xlsx")):
                    caminho_completo = os.path.join(root, nome_arquivo)
                    print(f"Testando arquivo: {caminho_completo}")
                    self.filtrar_dados(caminho_completo)
                    
    def filtrar_dados(self, caminho:str):
        try:
            if caminho.lower().endswith(".xlsx"):
                teste = pandas.read_excel(caminho)
            else:
                # O sep=None tenta detectar se é vírgula ou ponto-e-vírgula sozinho
                teste = pandas.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig") 
            
            colunas_texto = teste.select_dtypes(include=["object","string"]).columns
            termo_busca = "EVENTO|SINISTRO"
            mask_texto = teste[colunas_texto].apply(
                lambda col: col.str.contains(termo_busca, case=False, na=False)
            ).any(axis=1)

            if mask_texto.any():
                print(f"Alvo encontrado em {len(teste[mask_texto])} linhas")
                nome = os.path.basename(caminho)
                dados_normalizados = self.normalizar(teste, nome)
                self.dados_consolidados.append(dados_normalizados)
            else:
                print("Arquivo sem termos de sinistros/eventos.")
            
        except Exception as e:
            print(f"Erro ao ler {caminho}: {e}")  
            
    def normalizar(self, df: pandas.DataFrame, nome_original):

        try:
            # 1. Limpeza de colunas
            df.columns = df.columns.str.strip().str.upper().str.replace('"', "")
            df = df.loc[:, ~df.columns.duplicated()].copy()

            # 2. Mapeamento para normalização 
            mapeamento = {}
            for col in df.columns:
                if "DATA" in col or "DT_" in col: mapeamento[col] = "DATA_BASE"
                elif "REG" in col or "ANS" in col: mapeamento[col] = "REGISTRO_OPERADORA"
                elif "CD_CONTA" in col or "CONTABIL" in col: mapeamento[col] = "CODIGO_CONTABIL" 
                elif "DESC" in col: mapeamento[col] = "DESCRICAO"
                elif "INICIAL" in col or "INI" in col: mapeamento[col] = "V_INICIAL"
                elif "FINAL" in col or "FIN" in col: mapeamento[col] = "V_FINAL"

            df = df.rename(columns=mapeamento)

            # 3 Conversão Numérica
            for v_col in ["V_INICIAL", "V_FINAL"]:
                if v_col in df.columns:
                    # Remove pontos de milhar, troca vírgula por ponto e converte
                    df[v_col] = pandas.to_numeric(
                        df[v_col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False), 
                        errors="coerce"
                    ).fillna(0)
                    
            # 4 Filtro para a contabilidade não contar duplicado 
            
            df['CODIGO_CONTABIL'] = df['CODIGO_CONTABIL'].astype(str).str.strip()
            df = df.sort_values('CODIGO_CONTABIL').reset_index(drop=True)
            
            # Algoritmo: Se o próximo código na lista começar com o atual, o atual é PAI (totalizador)
            codes = df['CODIGO_CONTABIL'].tolist()
            is_leaf = [not (i + 1 < len(codes) and codes[i+1].startswith(codes[i])) for i in range(len(codes))]
            df = df[is_leaf].copy()
            
            # 5. Cálculo e Filtro Final
            if "V_FINAL" in df.columns and "V_INICIAL" in df.columns:
                df["VALOR_DESPESAS"] = df["V_FINAL"] - df["V_INICIAL"]
                df_final = df[df["VALOR_DESPESAS"] > 0].copy()
                
                cols_finais = [
                    "REGISTRO_OPERADORA", "DATA_BASE", "CODIGO_CONTABIL", 
                    "DESCRICAO", "V_INICIAL", "V_FINAL", "VALOR_DESPESAS"
                ]
                
                cols_existentes = [c for c in cols_finais if c in df_final.columns]
                df_saida = df_final[cols_existentes]

                nome_base = nome_original.split(".")[0]
                caminho_final = os.path.join(self.saida, f"{nome_base}_normalizado.csv")
                
                os.makedirs(self.saida, exist_ok=True)
                df_saida.to_csv(caminho_final, index=False, sep=";", encoding="utf-8-sig")
                
                print(f"Arquivo completo salvo em: {caminho_final}")
                return df_saida
            
            return None
        except Exception as e:
            print(f" Falha na normalização: {e}")
            return None
    def consolidar_e_salvar(self, caminho_cadastro):
        if not self.dados_consolidados:
            print(" Nenhum dado para consolidar.")
            return

        # Junta os trimestres processados
        df_final = pandas.concat(self.dados_consolidados, ignore_index=True)

        # Carrega o Cadastro (do link da ANS)
        df_cad = pandas.read_csv(caminho_cadastro, sep=";", encoding="utf-8-sig", dtype={"CNPJ":str})
        df_cad.columns = df_cad.columns.str.strip().str.upper()

        # Cruzamento de dados (JOIN)
        df_final = pandas.merge(
            df_final, 
            df_cad[["REGISTRO_OPERADORA", "CNPJ", "RAZAO_SOCIAL"]], 
            left_on="REGISTRO_OPERADORA", 
            right_on="REGISTRO_OPERADORA", 
            how="left"
        )
        
        #  Criando Ano e Trimestre a partir da DATA_BASE
        df_final["DATA_BASE"] = pandas.to_datetime(df_final["DATA_BASE"], errors="coerce")
        df_final["Ano"] = df_final["DATA_BASE"].dt.year
        df_final["Trimestre"] = df_final["DATA_BASE"].dt.quarter

        # Renomeando para bater com o requisito exato
        df_final = df_final.rename(columns={
            "VALOR_DESPESAS": "ValorDespesas",
            "RAZAO_SOCIAL": "RazaoSocial"
        })
        # Agrupar por CNPJ, Ano e Trimestre. 
        # Soma o ValorDespesas e pega a "primeira" RazaoSocial que encontrar
        df_agrupado = df_final.groupby(["CNPJ", "Ano", "Trimestre"]).agg({
            "ValorDespesas": "sum",
            "RazaoSocial": "first" # Resolve o problema de CNPJ com nomes diferentes
        }).reset_index()

        df_agrupado["ValorDespesas"] = df_agrupado["ValorDespesas"].round(2)
        
        # Seleciona colunas finais na ordem do requisito
        colunas_1_3 = ["CNPJ", "RazaoSocial", "Trimestre", "Ano", "ValorDespesas"]
        df_saida = df_agrupado[colunas_1_3]

        #  Salva CSV e Compacta em ZIP
        csv_path = os.path.join(self.saida, "consolidado_despesas.csv")
        zip_path = os.path.join(self.saida, "consolidado_despesas.zip")
        
        os.makedirs(self.saida, exist_ok=True)
        # utf-8-sig para o Excel abrir os acentos direto
        df_saida.to_csv(csv_path, index=False, sep=";", encoding="utf-8-sig")

        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(csv_path, arcname="consolidado_despesas.csv")
        
        print(f" CONSOLIDADO COM SUCESSO: {zip_path}")