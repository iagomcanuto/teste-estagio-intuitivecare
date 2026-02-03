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
                df = pandas.read_excel(caminho)
            else:
                # O sep=None tenta detectar se é vírgula ou ponto-e-vírgula sozinho
                df = pandas.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig") 
            
            df.columns = df.columns.str.strip().str.upper().str.replace('"', "")
            col_codigo = next((c for c in df.columns if "CD_CONTA" in c or "CONTABIL" in c), None)
            
            if col_codigo:
                df[col_codigo] = df[col_codigo].astype(str).str.strip()
                mask_411 = df[col_codigo].str.startswith('411')
                
                if mask_411.any():
                    df_filtrado = df[mask_411].copy()
                    nome = os.path.basename(caminho)
                    dados_normalizados = self.normalizar(df_filtrado, nome)
                    self.dados_consolidados.append(dados_normalizados)
                else:
                    print("Nenhum despesa com evento/sinistro encontrada")
            else:
                print("Coluna com codigo contabil nao encontrada")
            
        except Exception as e:
            print(f"Erro ao ler {caminho}: {e}")  
            
    def normalizar(self, df: pandas.DataFrame, nome_original):

        try:
            # Limpeza de colunas
            df = df.loc[:, ~df.columns.duplicated()].copy()

            # Mapeamento para normalização 
            mapeamento = {}
            for col in df.columns:
                if "DATA" in col or "DT_" in col: mapeamento[col] = "DATA_BASE"
                elif "REG" in col or "ANS" in col: mapeamento[col] = "REGISTRO_OPERADORA"
                elif "CD_CONTA" in col or "CONTABIL" in col: mapeamento[col] = "CODIGO_CONTABIL" 
                elif "DESC" in col: mapeamento[col] = "DESCRICAO"
                elif "INICIAL" in col or "INI" in col: mapeamento[col] = "V_INICIAL"
                elif "FINAL" in col or "FIN" in col: mapeamento[col] = "V_FINAL"

            df = df.rename(columns=mapeamento)

            # Conversão Numérica
            for v_col in ["V_INICIAL", "V_FINAL"]:
                if v_col in df.columns:
                    # Remove pontos de milhar, troca vírgula por ponto e converte
                    df[v_col] = pandas.to_numeric(
                        df[v_col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False), 
                        errors="coerce"
                    ).fillna(0)
                    
            # Filtro para a contabilidade não contar duplicado 
            
            df["CODIGO_CONTABIL"] = df["CODIGO_CONTABIL"].astype(str).str.strip()
            df = df.sort_values("CODIGO_CONTABIL").reset_index(drop=True)
            
            def obter_apenas_folhas(grupo:pandas.DataFrame):
                # Ordena as contas daquela operadora específica
                
                grupo = grupo.sort_values("CODIGO_CONTABIL")
                codes = grupo["CODIGO_CONTABIL"].astype(str).tolist()

                # Identifica se a próxima conta começa com a atual (se sim, a atual é "Pai")
                is_leaf = [
                    not (i + 1 < len(codes) and codes[i+1].startswith(codes[i])) 
                    for i in range(len(codes))
                ]
                return grupo[is_leaf]

            # Isso impede que uma operadora apague os dados da outra
            
            col_reg = next((c for c in df.columns if "REG_ANS" in c or "REGISTRO" in c), 'REG_ANS')
            df = df.groupby(col_reg, group_keys=True).apply(obter_apenas_folhas).reset_index()
            
            
            
            # Cálculo e Filtro Final
            if "V_FINAL" in df.columns and "V_INICIAL" in df.columns:
                df["VALOR_DESPESAS"] = df["V_FINAL"] - df["V_INICIAL"]
                df_final = df[df["VALOR_DESPESAS"] != 0].copy()
                
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

        # Evitar duplicados
        df_cad_extra = df_cad[["CNPJ", "MODALIDADE", "UF"]].drop_duplicates(subset="CNPJ")
        # Segundo join por CNPJ 
        df_final = pandas.merge(
            df_final, 
            df_cad_extra, 
            on="CNPJ", 
            how="left"
        )

        # Renomeia a coluna para bater com o requisito exato
        df_final = df_final.rename(columns={"REGISTRO_OPERADORA": "RegistroANS"})


        #  Criando Ano e Trimestre a partir da DATA_BASE
        df_final["DATA_BASE_TEMP"] = pandas.to_datetime(df_final["DATA_BASE"], errors="coerce")
        
        # Separando os erros para não perder dados depois do tratamento 
        mask_data_valida = df_final["DATA_BASE_TEMP"].notna()
        df_data_invalida = df_final[~mask_data_valida].copy()
        df_final = df_final[mask_data_valida].copy()
        
        df_final["DATA_BASE"] = df_final["DATA_BASE_TEMP"]
        df_final["Ano"] = df_final["DATA_BASE"].dt.year
        df_final["Trimestre"] = df_final["DATA_BASE"].dt.quarter
        df_final = df_final.drop(columns=["DATA_BASE_TEMP"])
        
        # Caso existam, dados invalidos serão separados em um log
        if not df_data_invalida.empty:
            log_path = os.path.join(self.saida, "log_datas_invalidas.csv")
            df_data_invalida.to_csv(log_path, index=False, sep=";", encoding="utf-8-sig")
            print(f" {len(df_data_invalida)} linhas com data inválida movidas para log.")

        # Renomeando para bater com o requisito exato
        df_final = df_final.rename(columns={
            "VALOR_DESPESAS": "ValorDespesas",
            "RAZAO_SOCIAL": "RazaoSocial"
        })
        # Agrupar por CNPJ, Ano e Trimestre. 
        # Soma o ValorDespesas e pega a "primeira" RazaoSocial que encontrar
        df_agrupado = df_final.groupby(["CNPJ", "Ano", "Trimestre", "RegistroANS", "MODALIDADE", "UF"]).agg({
            "ValorDespesas": "sum",
            "RazaoSocial": "first" # Resolve o problema de CNPJ com nomes diferentes
        }).reset_index()
        
        # Agora que a soma já foi feita (e os estornos descontados), 
        # Limpar quem ficou com saldo negativo ou zerado do relatório final.
        df_agrupado = df_agrupado[df_agrupado["ValorDespesas"] > 0].copy()

        df_agrupado["ValorDespesas"] = df_agrupado["ValorDespesas"].round(2)
        
        # Seleciona colunas finais na ordem do requisito
        colunas_1_3 = ["CNPJ", "RazaoSocial", "Trimestre", "Ano", "ValorDespesas", "RegistroANS", "MODALIDADE", "UF"]
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
        
    def gerar_despesas_agregadas(self, df_input:pandas.DataFrame):
        # Agrupamento principal por Operadora e UF
        # Como o df_input já está no nível de trimestres, 
        # a média aqui será automaticamente a 'Média por Trimestre'
        df_agregado = df_input.groupby(['RazaoSocial', 'UF']).agg({
            'ValorDespesas': ['sum', 'mean', 'std']
        }).reset_index()
        df_agregado.columns = [
            'RazaoSocial', 'UF', 'Total_Despesas', 
            'Media_Trimestral', 'Desvio_Padrao_Despesas'
        ]
        # Tratamento desvio padrão NaN
        # Se a operadora só tiver 1 trimestre, o desvio padrão é 0 (ou NaN)
        df_agregado['Desvio_Padrao_Despesas'] = df_agregado['Desvio_Padrao_Despesas'].fillna(0)
        # Ordenação in memory
        # Ordenar do maior Valor Total para o menor
        df_agregado = df_agregado.round(2)
        df_agregado = df_agregado.sort_values(by='Total_Despesas', ascending=False)
        caminho_csv = os.path.join(self.saida, "despesas_agregadas.csv")
        df_agregado.to_csv(caminho_csv, index=False, sep=";", encoding="utf-8-sig")
        # Compactação 
        nome_zip = "Teste_Iago_Meneses_Canuto.zip" 
        zip_path = os.path.join(self.saida, nome_zip)
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(caminho_csv, arcname="despesas_agregadas.csv")
        return df_agregado  