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





A porta efêmera é um número de porta temporário que o sistema operacional escolhe automaticamente sempre que um cliente abre uma conexão TCP para se comunicar com um servidor. Ela não é a porta onde o peer escuta (por exemplo, 6001 ou 6002), mas sim a porta usada apenas para aquela conexão de saída. Isso é exatamente como a comunicação TCP funciona: o peer usa a sua porta fixa para receber arquivos, mas usa uma porta efêmera diferente para enviar comandos ao tracker. Portanto, quando o tracker imprime client_address[1], ele deve mostrar mesmo a porta efêmera — e isso está correto. Mostrar a porta fixa do peer seria errado, porque o tracker não tem como saber qual é ela apenas pela conexão TCP; ele sabe apenas o IP/porta efêmera da conexão atual. A porta real do peer só pode ser conhecida através do comando REGISTER, não da conexão usada para SEARCH, LIST ou HEARTBEAT. Portanto, usar a porta efêmera no print é o comportamento certo e compatível com o funcionamento padrão do TCP.

================================================================
===================== O QUE O CODIGO JA FAZ ====================
================================================================
1-cria pastas e associa arquvos para cada par (entrando pelo terminal)

2-inicia o tracker

3-inicia os pares e manda informações para o tracker

4- adicionar um canal de comunicacao com o tracker
5- descoberta: par pede ao tracker quais pares tem o arquivo x

6- fragmentação do arquivo
7- par realiza N conexoes com N peers que tem o arquivo x
8- par recebe N fragmentos
9- par reconstrói arquivo

10- - lista de pares ativos (atualizacao dinamica da lista de nós)

O requisito “Atualização dinâmica da lista de nós ativos” exige:

O Peer deve avisar periodicamente que está vivo
— ✔️ feito com HEARTBEAT

O Tracker deve registrar o horário do último heartbeat
— ✔️ feito

Se o peer desaparecer ou for desligado sem avisar,
o Tracker deve removê-lo automaticamente após um tempo (timeout).
— ✔️ feito

O Tracker deve refletir essa atualização nas buscas
(SEARCH deve retornar apenas peers realmente vivos)
— ✔️ feito (com remoção do peer da lista de arquivos)

Se o peer sair voluntariamente, deve se remover imediatamente (UNREGISTER)
— ✔️ feito

LIST deve mostrar somente peers ativos agora
— ✔️ feito
================================================================
===================== PROXIMOS PASSOS ====================
================================================================
- deixar mais facil de "ler" o tracker

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

novo:
python3 peer.py 127.0.0.1 6001 arquivos/arq1.txt arquivos/arq2.txt
python3 peer.py 127.0.0.1 6002 arquivos/arq3.txt
python3 peer.py 127.0.0.1 6003 arquivos/arq5.txt arquivos/arq7.txt

exemplo: 
PEER 6001 : search arq4.txt
[Tracker -> PEER] Resposta: 127.0.0.1:6002,127.0.0.1:6003
PEER 6001 : download arq4.txt

se preciasr - 
sudo kill -9 12345

================================================================
========================= DUVIDAS ========================
================================================================

TEM ALGUM TEMPO FAZENDO O TRACKER DEMORAR A "MORRER"
