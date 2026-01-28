from src.coletorANS import coletorANS
#from src.processador_dados import processador_dados

def main():
    coletor = coletorANS()
    coletor.executar()

if __name__ == "__main__":
    main()