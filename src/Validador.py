import os 
import pandas
import re
class Validador:
    
    def __init__(self, caminho_consolidado, pasta_saida):
        self.df = pandas.read_csv(caminho_consolidado, sep=';', dtype={'CNPJ': str}, encoding='utf-8-sig')
        self.pasta_saida = pasta_saida
        os.makedirs(self.pasta_saida, exist_ok=True)
        

    def validar_cnpj(self,cnpj):
        # Remove caracteres não numéricos e garante 14 dígitos
        cnpj = re.sub(r'\D', '', str(cnpj)).zfill(14)

        # Bloqueia sequências repetidas (ex: 00000000000000)
        if len(cnpj) != 14 or cnpj in [s * 14 for s in '0123456789']:
            return False

        def calcular_digito(fatia, pesos):
            soma = sum(int(a) * b for a, b in zip(fatia, pesos))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)

        # Pesos oficiais da Receita Federal
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        digito_1 = calcular_digito(cnpj[:12], pesos_1)
        digito_2 = calcular_digito(cnpj[:13], pesos_2)

        return cnpj[-2:] == (digito_1 + digito_2)
    
    def executar_limpeza(self):
        
        # Validação de Razão Social e CNPJ
        mask_razao = self.df['RazaoSocial'].notna() & (self.df['RazaoSocial'].str.strip() != "")
        mask_cnpj = self.df['CNPJ'].apply(self.validar_cnpj)

        mask_final = mask_razao & mask_cnpj

        # Segregação dos dados
        df_valido = self.df[mask_final].copy()
        df_invalido = self.df[~mask_final].copy()

        # Salva o log para auditoria se houver erros
        if not df_invalido.empty:
            log_path = os.path.join(self.pasta_saida, "log_erros_validacao_2_1.csv")
            df_invalido.to_csv(log_path, index=False, sep=";", encoding="utf-8-sig")
            print(f"{len(df_invalido)} registros inválidos movidos para o log.")

        # Salva o arquivo final para a análise estatística
        caminho_final = os.path.join(self.pasta_saida, "consolidado_final_limpo.csv")
        df_valido.to_csv(caminho_final, index=False, sep=";", encoding="utf-8-sig")
        
        print(f"Dados validados e salvos em: {caminho_final}")
        return df_valido