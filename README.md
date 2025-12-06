# redes_P2P

3. Arquitetura P2P para Compartilhamento de Arquivos (3 )
Rede Peer-to-Peer Simples
Descrição: Crie uma aplicação P2P onde cada nó pode atuar como cliente e servidor, compartilhando arquivos diretamente com outros pares.

Requisitos:
Descoberta de pares na rede (P2P discovery).

Solicitação e envio de arquivos entre pares.

Atualização dinâmica da lista de nós ativos.


Incrementos:
(Desempenho): Implementar cache de blocos mais acessados.

(Segurança): Assinatura digital dos blocos compartilhados.

================================================================


================================================================
EXPLICACOES
================================================================

O PEERS_LOCK é um objeto do tipo treading.Lock e funciona como um semáforo ou uma chave de acesso exclusiva.
O tracker usa treading para lidar com varios peers ao mesmo tempo. Nesse contexto, pode acontecer uma condição de corrida. 

quando criar o peer quero:
receber endereco - IP - lista de arquivos que ele tem acesso

================================================================
===================== O QUE O CODIGO JA FAZ ====================
================================================================
1-cria pastas e associa arquvos para cada par (melhora isso depois - passar arquivos na entrada e ele cria a pasta com eles)

2-inicia o tracker

3-inicia os pares e manda informações para o tracker

4- adicionar um canal de comunicacao com o tracker
5- descoberta: par pede ao tracker quais pares tem o arquivo x

6- fragmentação do arquivo
7- par realiza N conexoes com N peers que tem o arquivo x
8- par recebe N fragmentos
9- par reconstrói arquivo
================================================================
===================== PROXIMOS PASSOS ====================
================================================================
- entrar arquivos que o peer tem pelo terminal e nao do jeito que ta

- lista de pares ativos (atualizacao dinamica da lista de nós)

- (Segurança): Assinatura digital dos blocos compartilhados.
================================================================
========================= COMO COMPILAR ========================
================================================================

exemplo:
python3 setup_files.py
terminal 1: 
python3 tracker.py
terminal 2: 
python3 peer.py 127.0.0.1 6001 peers_data/peer_6001
terminal 3: 
python3 peer.py 127.0.0.1 6002 peers_data/peer_6002
python3 peer.py 127.0.0.1 6003 peers_data/peer_6003

exemplo: 
PEER 6001 : search arq4.txt
[Tracker -> PEER] Resposta: 127.0.0.1:6002,127.0.0.1:6003
PEER 6001 : download arq4.txt

================================================================
========================= DUVIDAS ========================
================================================================

sera q é melhor eu passar os arquivos em vez de passar o "peers_data/peer_601"? sim

quando eu busco um arquivo o tracker resposde de todos os pares (inclusive aqueles que ja estao desconectados)?????? pois é, tem q arrumar isso