import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from src.Downloader import Downloader

class ColetorANS:
    def __init__(self, url_base, area_alvo, diretorio):
        self.url_base = url_base
        self.area_alvo = area_alvo
        self.diretorio = diretorio 
        self.downloader = Downloader(self.diretorio)

    def buscar_dados(self):
        quantidade_dados = 0
        quantidade_desejada = 3
        
        link_alvo = self.requisicao_unica(self.url_base, self.area_alvo)    
        url_anos = self.requisicao_multipla(link_alvo)        
        url_anos.reverse()
        
    # Selecionar dentro da pagina o ano mais recente usando ordem decrescente do conteudo 
        
        for ano in url_anos:
            if quantidade_dados >= quantidade_desejada:
                break
            
            link_do_ano = self.requisicao_unica(link_alvo, ano)
            if link_do_ano:
                print(f"Buscando em {ano}")
                arquivos = self.requisicao_multipla(link_do_ano)
                
                for arq_link in arquivos:
                    if "zip" in arq_link.lower():
                        url_completa = urljoin(link_do_ano, arq_link)
                        if self.downloader.baixar(url_completa):
                            quantidade_dados += 1
                    
                    if quantidade_dados >= quantidade_desejada:
                        break
    # Mexer na resiliencia dessa lógica para para prever diferentes organizações de pastas            
        
    def requisicao_unica(self, url, alvo):
        
    # Tenta acessar a url fornecida caso consiga retorna o codigo 200, caso não dispara um erro 
    # Retorna um link de certa pagina 
    
        try:
            request = requests.get(url, timeout= 5)
            print(f"O status do requerimento da url {url} foi: {request.status_code}")
            request.raise_for_status()
            tradutor = BeautifulSoup(request.text, "html.parser")
            area_alvo = alvo
            link_alvo = None
            for link in tradutor.find_all('a'):
                link_real = link.get("href")
                if link_real and area_alvo in link_real:
                    link_alvo = urljoin(url,link_real)            
                    return link_alvo
            return None
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexao ou resposta {e}")
            return None
        
    def requisicao_multipla(self,url):
            
    # retorna todos os links de dada pagina
            
        try:
            request = requests.get(url, timeout= 5)
            print(f"O status do requerimento da url {url} foi: {request.status_code}")
            request.raise_for_status()
            tradutor = BeautifulSoup(request.text, "html.parser")
            return [link.get("href") for link in tradutor.find_all('a') if link.get("href")]
        except requests.exceptions.RequestException as e:
             print(f"Erro de conexao ou resposta {e}")
             return []
         
    def baixar_dados(self, local_dados):
        
        url_dados = self.requisicao_multipla(local_dados)  
        
        for dado in url_dados:
            arquivo = urljoin (local_dados, dado)
            extensoes_alvo = ('.zip', '.csv', '.xlsx', '.rar', '.txt', '.pdf')
            if dado.lower().endswith(extensoes_alvo):
                self.downloader.baixar(arquivo)
        