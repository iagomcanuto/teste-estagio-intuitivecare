import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from src.Downloader import Downloader

class ColetorANS:
    def __init__(self, url_base, area_alvo, diretorio, quantidade_desejada):
        self.url_base = url_base
        self.area_alvo = area_alvo
        self.diretorio = diretorio 
        self.downloader = Downloader(self.diretorio)
        self.quantidade_desejada = quantidade_desejada
        self.quantidade_dados = 0

    def buscar_dados(self):
        
        link_alvo = self.requisicao_unica(self.url_base, self.area_alvo)
        if not link_alvo:
            print("Link nao encontrado")
            return
        self.explorar_recursivo(link_alvo)          
        
    def requisicao_unica(self, url, alvo):
        
    # Tenta acessar a url fornecida caso consiga retorna o codigo 200, caso não dispara um erro 
    # Retorna um link de certa pagina 
    
        try:
            request = requests.get(url, timeout= 5)
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
                
    def explorar_recursivo(self,url):
        extensoes_alvo = ('.zip', '.csv', '.xlsx')
        if self.quantidade_dados >= self.quantidade_desejada:
            return
        
        url_elemento = self.requisicao_multipla(url)        
        url_elemento.reverse()
        
    # Selecionar dentro da pagina o elemento mais recente usando ordem decrescente do conteudo 
        for elemento in url_elemento:
            if self.quantidade_dados >= self.quantidade_desejada:
                break
            
            link_do_elemento = urljoin(url, elemento)
            if elemento.endswith('/') or '.' not in elemento:
                print(f"Entrando na pasta: {elemento}")
                self.explorar_recursivo(link_do_elemento)

            elif elemento.lower().endswith(extensoes_alvo):
                print(f"Arquivo ZIP encontrado: {elemento}")
                if self.downloader.baixar(link_do_elemento):
                    self.quantidade_dados += 1
