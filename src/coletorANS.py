import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import datetime

class coletorANS:

    def __init__(self, diretorio = "data/raw"):
        self.diretorio = diretorio
        self.url_base = "https://dadosabertos.ans.gov.br/FTP/PDA/"
        os.makedirs(self.diretorio, exist_ok=True)


    def executar(self):
        
        print(f"Acessando a url: {self.url_base}")
        self.buscar_dados()

    def buscar_dados(self):
        quantidade_dados = 3
        try:

    # Tenta acessar a url fornecida caso consiga retorna o codigo 200, caso não dispara um erro 

            request = requests.get(self.url_base, timeout= 5)
            print(f"O status do requerimento foi: {request.status_code}")
            request.raise_for_status()

    # O metodo get da da biblioteca requests me devolve os dados da pagina para então extração dos links

            tradutor = BeautifulSoup(request.text, "html.parser")

    # usar a biblioteca para separar os links e selecionar a pagina expecifica demonstracoes_contabeis

            area_alvo = "demonstracoes_contabeis"
            link_alvo = None
            for link in tradutor.find_all('a'):
                #texto_do_link = link.get_text()
                link_real = link.get("href")
                # print(f"{texto_do_link}")
                if area_alvo in link_real:
                    link_alvo = urljoin(self.url_base,link_real)
                    break
            request_pagina = requests.get(link_alvo, timeout=5)
            request_pagina.raise_for_status()
            tradutor2 = BeautifulSoup(request_pagina.text, "html.parser")

            ano_busca = datetime.date.today().year
            quantidade_desejada = 0
    # Selecionar dentro da pagina o ano mais recente partindo do ano atual e chamar o metodo para baixar o conteudo 
            while ano_busca > 2000 and quantidade_desejada < quantidade_dados:
                link = None
                for link in tradutor2.find_all('a'):
                    demonstracao_ano = link.get_text()
                    if str(ano_busca) in demonstracao_ano:
                        print(f"Buscando em {ano_busca}")
                        link_ano = urljoin(link_alvo,link.get("href"))
                        break
                if str(ano_busca) not in link.get_text():
                    ano_busca -= 1
                    continue  

                request_ano = requests.get(link_ano, timeout= 5 )
                request_ano.raise_for_status()
                request_ano_tradutor = BeautifulSoup(request_ano.text, "html.parser")
                for link in request_ano_tradutor.find_all("a"):
                    link_disponivel = link.get("href")
                    print(f"{link_disponivel}")
    # Logica de baixar o conteudo ---- Continuar Daqui ---- passar essa lógica para uma classe ou metodo separado e aumentar a resiliencia para outros tipos de arquivo 
                    if ".zip" in link_disponivel:
                        print(f"Arquivo encontrado {link_disponivel}")
                        url_completa_zip = urljoin(link_ano, link_disponivel)
                        request_arquivo = requests.get(url_completa_zip, stream= True)
                        request_arquivo.raise_for_status()
                        caminho = os.path.join(self.diretorio,link_disponivel)
                        with open(caminho,"wb") as f:
                            for chunk in request_arquivo.iter_content(chunk_size=8200):
                                f.write(chunk)
                        print(f"Baixando arquivos em {caminho}")
                        quantidade_desejada += 1
                        if quantidade_desejada >= quantidade_dados:
                            break
                ano_busca -= 1             

        except requests.exceptions.RequestException as e:
            print(f"Erro de conexao ou resposta {e}")
            return None