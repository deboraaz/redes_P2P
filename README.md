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

melhorar:
- armazenamento dinamico!

como rodar ate agora:
    ./tracker 5000
    ./peer 127.0.0.1 5000 6001
    ./peer 127.0.0.1 5000 6002

próximos passos:
ok definir quais arquivos usar
- associar aruqivos aos pares (como associar?)

- descoberta: par pede ao tracker quais pares tem o arquivo x

- fragmentação do arquivo
- par inicia N conexoes 
- par recebe N fragmentos
- par reconstrói arquivo

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
cria os pares 

================================================================
========================= COMO COMPILAR ========================
================================================================

exemplo:

terminal 1: python3 tracker.py
terminal 2: python3 peer.py 127.0.0.1 6001 peers_data/peer_6001
terminal 3: python3 peer.py 127.0.0.1 6002 peers_data/peer_6002


================================================================
========================= DUVIDAS ========================
================================================================

sera q é melhor eu passar os arquivos em vez de passar o "peers_data/peer_601"?