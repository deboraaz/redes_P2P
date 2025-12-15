import socket
import threading
import time #para uso do heartbeat


# Dicionário global para armazenar informações dos peers
PEERS = {} # estrutura chave valor: "ip:port" : {"ip": ip, "port": port, "files": []}
peer_last_seen = {} # estrutura chave valor: "ip:port" : timestamp do ultimo heartbeat recebido

PEERS_LOCK = threading.Lock() #iniciada globalmente para evitar problemas de concorrencia

# Função para lidar com a conexão de um peer 
# REGISTER, SEARCH, UNREGISTER, LIST, HEARTBEAT, UPDATE
def handle_peer_conection(client_socket, client_address):
    try:
        #recebe os dados do peer
        data = client_socket.recv(1024).decode('utf-8').strip()
    
        if not data:
            print(f"[TRACKER] Mensagem vazia de {client_address}")
            return
        
        parts_data = data.split() #divide a string em partes

        if len(parts_data) == 0:
            print(f"[TRACKER] Mensagem inválida de {client_address}: '{data}'")
            return

        command = parts_data[0] #comando recebido do peer

        if command == "REGISTER":
            peer_ip = parts_data[1]
            peer_port = int(parts_data[2])

            if len(parts_data) > 3:
                files = parts_data[3].split(",") 
            else:
                files = []
            
            peer_id = f"{peer_ip}:{peer_port}"
            
            with PEERS_LOCK:
                PEERS[peer_id] = {"ip": peer_ip, "port": peer_port, "files": files}
                peer_last_seen[peer_id] = time.time() 
            print(f"[TRACKER] Peer registrado: {peer_id}")
            
        elif command == "SEARCH":
            if len(parts_data) < 2:
                print(f"[TRACKER] SEARCH inválido recebido de {client_address}: '{data}'")
                client_socket.sendall(b"ERRO: SEARCH requer nome do arquivo")
                return
            
            filename = parts_data[1]

            result = [] # lista de peers que possuem o arquivo

            # loop que varre os peer procurando o arquivo
            with PEERS_LOCK:
                for peer_key, peer_info in PEERS.items():
                    if filename in peer_info["files"]:
                        result.append(peer_key)
            if result:
                responde = ','.join(result) # junta os peers que possuem o arquivo
            else:
                responde = "NAO ENCONTRADO"

            client_socket.sendall(responde.encode('utf-8'))
            print(f"[TRACKER] Lista de pares com o arquivo '{filename}' enviada ao peer {client_address}")

        elif command == "UNREGISTER":
            peer_ip = parts_data[1]
            peer_port = parts_data[2]
            peer_id = f"{peer_ip}:{peer_port}"
            
            with PEERS_LOCK:
                if peer_id in PEERS:
                    del PEERS[peer_id]
                if peer_id in peer_last_seen:
                    del peer_last_seen[peer_id]
            print(f"[TRACKER] Peer unregistered: {peer_id}")

        elif command == "LIST":
            # Retorna a lista atual de keys de peers ativos
            with PEERS_LOCK:
                keys = list(PEERS.keys()) 
            resp = ",".join(keys) if keys else ""
            client_socket.sendall(resp.encode('utf-8'))
            print(f"[TRACKER] Enviada lista de peers ativos para {client_address}: {resp}")

        elif command == "HEARTBEAT":
            ip = parts_data[1]
            port = parts_data[2]
            peer_id = f"{ip}:{port}"
            with PEERS_LOCK:
                peer_last_seen[peer_id] = time.time()
        elif command == "UPDATE":
            ip = parts_data[1]
            port = parts_data[2]
            file_name = parts_data[3]
            
            peer_id = f"{ip}:{port}"

            with PEERS_LOCK:
                if peer_id in PEERS:
                    if file_name not in PEERS[peer_id]["files"]:
                        PEERS[peer_id]["files"].append(file_name)
                else:
                    client_socket.sendall(b"ERRO Peer nao registrado")

    except Exception as e:
        print(f"[TRACKER] Erro ao lidar com conexão do peer {client_address}: {e}")
    finally:
        client_socket.close()

def cleanup_dead_peers(peers, peer_last_seen, timeout=20):
    while True:
        now = time.time()
        to_remove = []

        with PEERS_LOCK:
            for peer_key, last in list(peer_last_seen.items()):
                if now - last > timeout:
                    to_remove.append(peer_key)

            for peer_key in to_remove:
                print(f"[TRACKER] Removendo peer inativo: {peer_key}")

                # remove do dict global
                if peer_key in peers:
                    del peers[peer_key]

                # remove do last_seen
                if peer_key in peer_last_seen:
                    del peer_last_seen[peer_key]
        time.sleep(10) #verifica a cada 10 segundos

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

# Responde a mensagens DISCOVER_TRACKER via UDP (para comunicacao entre maquinas distintas)
def tracker_discovery_responder(ip, port=5500):
    """
    Responde a mensagens DISCOVER_TRACKER via UDP.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))

    print(f"[TRACKER] Discovery UDP ativo em 0.0.0.0:{port}")

    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"DISCOVER_TRACKER":
            #local_ip = get_local_ip()
            msg = f"TRACKER_HERE {addr[0]} 5000".encode()
            sock.sendto(msg, addr)

def start_tracker(host='127.0.0.1', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permitir reutilizar a porta do tracker imediatamente (nos testes estava demorando quase um minuto)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"[TRACKER] Tracker iniciado em {host}:{port}. Aguardando conexões de peers...")

    # INICIA LIMPEZA AUTOMÁTICA
    cleanup_thread = threading.Thread(target=cleanup_dead_peers, args=(PEERS, peer_last_seen), daemon=True)
    cleanup_thread.start()

    while True:
        try:
            client_socket, client_address = server_socket.accept()

            #cria uma nova thread para lidar com cada conexao de peer
            peer_thread = threading.Thread(target=handle_peer_conection, args=(client_socket, client_address))
            peer_thread.start()
        except Exception as e:
            print(f"[TRACKER] Erro ao aceitar conexão: {e}")

if __name__ == "__main__":

    # detecta automaticamente o IP da máquina
    # hostname = socket.gethostname()
    # local_ip = socket.gethostbyname(hostname)

    TRACKER_IP = get_local_ip()

    # print(f"[TRACKER] IP detectado: {local_ip}")
    print(f"[TRACKER] Iniciado em: {TRACKER_IP}:5000")

    #start_tracker(host='127.0.0.1', port=5000)
    #tenho que usar 0.0.0.0 para t = threadingaceitar conexoes externas

    # thread de discovery UDP
    t = threading.Thread(target=tracker_discovery_responder, args=(TRACKER_IP,), daemon=True)
    t.start()

    start_tracker(host='0.0.0.0', port=5000)