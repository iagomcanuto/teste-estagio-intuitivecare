from src.ColetorANS import ColetorANS
from src.ProcessadorArquivo import ProcessadorArquivo

def main():
    url = "https://dadosabertos.ans.gov.br/FTP/PDA/"
    area = "demonstracoes_contabeis"
    diretorio = "data/raw"
    coletor = ColetorANS(url, area, diretorio)
    coletor.buscar_dados()
    coletor.baixar_dados("https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/")
    processador = ProcessadorArquivo()
    processador.extrair_todos()

if __name__ == "__main__":
    main()