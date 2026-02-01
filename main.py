from src.ColetorANS import ColetorANS
from src.ExtratorArquivo import ExtratorArquivo
from src.ProcessadorArquivo import ProcessadorArquivo

def main():
    url = "https://dadosabertos.ans.gov.br/FTP/PDA/"
    area = "demonstracoes_contabeis"
    diretorio = "data/raw"
# 1.1. Acesso à API de Dados Abertos da ANS
    coletor = ColetorANS(url, area, diretorio)
    coletor.buscar_dados()
    coletor.baixar_dados("https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/")
    extrator = ExtratorArquivo()
    extrator.extrair_todos()
# 1.2. Processamento de Arquivos
    pasta_entrada = "data/raw"
    pasta_saida = "data/output"
    processador = ProcessadorArquivo(pasta_saida, pasta_entrada)
    processador.abrir_arquivo()
# 1.3. Consolidação e Análise de Inconsistências
    caminho_cad = "data/raw/Relatorio_cadop.csv" 
    processador.consolidar_e_salvar(caminho_cad)
    
if __name__ == "__main__":
    main()