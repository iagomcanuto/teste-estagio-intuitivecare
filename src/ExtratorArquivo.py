import zipfile
import os

class ExtratorArquivo:
    def __init__(self, pasta_origem="data/raw", pasta_destino="data/raw"):
        self.pasta_origem = pasta_origem
        self.pasta_destino = pasta_destino
        os.makedirs(self.pasta_destino, exist_ok=True)

    def extrair_todos(self):
        
    # extrai todos os arquivos .zip encontrados.
    
        arquivos = [dado for dado in os.listdir(self.pasta_origem) if dado.endswith('.zip')]
        
        if not arquivos:
            print("Nenhum arquivo ZIP encontrado para extração.")
            return

        for arquivo in arquivos:
            caminho_zip = os.path.join(self.pasta_origem, arquivo)
            
    # Cria uma subpasta com o nome do arquivo (sem o .zip) para não misturar tudo
    
            subpasta_extracao = os.path.join(self.pasta_destino, arquivo.replace('.zip', ''))
            
            try:
                with zipfile.ZipFile(caminho_zip, 'r') as zip:
                    print(f"Extraindo: {arquivo}")
                    zip.extractall(subpasta_extracao)
                print(f"Conteúdo de {arquivo} extraído para {subpasta_extracao}")
            except zipfile.BadZipFile:
                print(f"Erro: O arquivo {arquivo} está corrompido.")
            except Exception as e:
                print(f"Erro inesperado ao extrair {arquivo}: {e}")
    
    