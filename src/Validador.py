import os 
import pandas

class Validador:
    
  def __init__(self, caminho_consolidado, pasta_saida):
        self.df = pandas.read_csv(caminho_consolidado, sep=';', dtype={'CNPJ': str}, encoding='utf-8-sig')
        self.pasta_saida = pasta_saida
        os.makedirs(self.pasta_saida, exist_ok=True)
        
