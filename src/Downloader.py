import requests
import os

class Downloader:
    def __init__(self,diretorio):
        self.diretorio = diretorio
        # Garante que a pasta exista logo de cara
        os.makedirs(self.diretorio, exist_ok=True)

    def baixar(self, url):
        print(f"Tentando baixar {url}")
        if not url:
            print("URL inválida")
            return False

        try:
            # Extrai o nome do arquivo da URL
            nome_arquivo = url.split('/')[-1].split('?')[0]
            caminho_final = os.path.join(self.diretorio, nome_arquivo)

            # Requisita o arquivo com stream=True
            
            with requests.get(url, stream=True, timeout=20) as r:
                r.raise_for_status() 
                with open(caminho_final, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=16384):
                        if chunk: # Filtra chunks vazios
                            f.write(chunk)
            
            return True

        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar {url}: {e}")
            return False
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")
            return False