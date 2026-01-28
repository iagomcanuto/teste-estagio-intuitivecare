import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class coletorANS:

    def __init__(self, diretorio = "data/raw"):
        self.diretorio = diretorio
        self.url_base = "https://dadosabertos.ans.gov.br/FTP/PDA/"
        os.makedirs(self.diretorio, exist_ok=True)


    def executar(self):
        
        print(f"Acessando a url: {self.url_base}")
        self.buscar_dados()

    def buscar_dados(self):
        try:

    # Tenta acessar a url fornecida caso consiga retorna o codigo 200, caso não dispara um erro 

            request = requests.get(self.url_base, timeout= 5)
            print(f"O status do requerimento foi: {request.status_code}")
            request.raise_for_status()

    # O metodo get da da biblioteca requests me devolve os dados da pagina para então extração dos links

            tradutor = BeautifulSoup(request.text, "html.parser")

    # -------- Continuar daqui ------- usar a biblioteca para separar os links e selecionar a pagina expecifica demonstracoes_contabeis
       
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexao ou resposta {e}")
            return None