# Arquivo P2P para comprtilhamento de arquivos

Este projeto implementa um sistema Peer-to-Peer (P2P) capaz de registrar peers em um servidor Tracker, solicitar lista de peers ativos, buscar arquivos, realizar download dividido em chunks e permitir a comunicação simultanea entre múltiplos pares. 

# Tecnologia utilizadas
    Linguagem python

    Bibliotecas:
        - socket     : comunicação TCP
        - threading  : realização de conexões simultâneas
        - os         : manipulaçao de arquivos
        - time       : monitoramento (heartbeat)
        - pathlib    : manipulação de caminhos
        - sys        : receber argumentos da linha de comando
        - shutil     : operações de cópia/movimentação de arquivos

# Como executar e testar

1- Clone o repositório e entre na pasta

    git clone https://github.com/deboraaz/redes_P2P.git
    cd redes_P2P

3 - Execute o tracker
    python3 tracker.py

4 - Execute peer (quantos quiser)

    python3 peer.py <endereço_ip> <porta> <lista_de_arquivos>

    Exemplo usando os arquivos da pasta "arquivos" 
    python3 peer.py 127.0.0.1 6001 arquivos/arq1.txt arquivos/arq2.txt
    python3 peer.py 127.0.0.1 6002 arquivos/arq3.txt
    python3 peer.py 127.0.0.1 6003 arquivos/arq5.txt arquivos/arq7.txt

# Funcionalidades implementadas
- Tracker
    - Registro de peers
    - Remoção de peers
    - Busca por arquivos
    - Envio da lista de peers ativos
    - Recebimento de heartbeat para monitoramento

- Peer
    - Registro no tracker
    - Lista de pares ativos na rede
    - Busca de arquivos
    - Download de arquivos:
        Escuta em porta efêmera
        Downloads por chunks(Impressão informando qual par enviou qual chunk)

# Possíveis melhorias

Implementar o incremento de segurança, adicionando assinatura digital dos blocos compartilhados. Assim, será possível garantir a integridade e a autenticidade dos arquivos transmitidos entre pares, evitando alterações maliciosas e aumentando a confiabilidade do sistema P2P.

consigo registrar um peer sem arquivos?

OBS.: quando ele vai pegar o tamanho do arquivo e ja fizeram varios downloads (ele sempre pega o primeiro da lista) mas se o primeiro da lista for alguem que fez download (e nao tinha desde a inicializacao) da problema pra encontrar o tamanho