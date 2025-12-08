import socket
import threading
import time #para uso do heartbeat

PEERS = {}
peer_last_seen = {} 

PEERS_LOCK = threading.Lock() #iniciada globalmente para evitar problemas de concorrencia

def handle_peer_conection(client_socket, client_address):
    try:
        #recebe os dados do peer
        data = client_socket.recv(1024).decode('utf-8').strip()
    
        if not data:
            print(f"[TRACKER] Mensagem vazia de {client_address}")
            return
        
        parts = data.split() #divide a string em partes

        if len(parts) == 0:
            print(f"[TRACKER] Mensagem inválida de {client_address}: '{data}'")
            return

        command = parts[0] #comando recebido do peer

        if command == "REGISTER":
            peer_ip = parts[1]
            peer_port = int(parts[2])

            files = parts[3].split(",") if len(parts) > 3 else []
            
            peer_address_key = f"{peer_ip}:{peer_port}"
            
            with PEERS_LOCK:
                PEERS[peer_address_key] = {"ip": peer_ip, "port": peer_port, "files": files}
                peer_last_seen[peer_address_key] = time.time()

            print(f"[TRACKER] Peer registrado: {peer_address_key}")
            client_socket.sendall(b"OK")

            
        elif command == "SEARCH":
            if len(parts) < 2:
                print(f"[TRACKER] SEARCH inválido recebido de {client_address}: '{data}'")
                client_socket.sendall(b"ERRO: SEARCH requer nome do arquivo")
                return
            
            filename = parts[1]
            #print(f"[TRACKER] Peer {client_address} está buscando pelo arquivo: {filename}")

            result = []

            with PEERS_LOCK:
                for peer_key, peer_info in PEERS.items():
                    if filename in peer_info["files"]:
                        result.append(peer_key)
            if result:
                responde = ','.join(result) # junta os peers que possuem o arquivo
            else:
                responde = "NAO ENCONTRADO"

            client_socket.sendall(responde.encode('utf-8'))
            # print(f"[TRACKER] Resposta enviada ao peer {client_address}: {responde}")
            print(f"[TRACKER] Lista de pares com o arquivo '{filename}' enviada ao peer {client_address}")

            # print(f"[TRACKER] Peer {client_address}(porta:{peer_port}) está buscando pelo arquivo: {filename}")
        elif command == "UNREGISTER":
            peer_ip = parts[1]
            peer_port = parts[2]
            peer_key = f"{peer_ip}:{peer_port}"
            with PEERS_LOCK:
                if peer_key in PEERS:
                    del PEERS[peer_key]
                if peer_key in peer_last_seen:
                    del peer_last_seen[peer_key]
            print(f"[TRACKER] Peer unregistered: {peer_key}")
            client_socket.sendall(b"OK")

        elif command == "LIST":
            # Retorna a lista atual de keys de peers ativos
            with PEERS_LOCK:
                keys = list(PEERS.keys())
            resp = ",".join(keys) if keys else ""
            client_socket.sendall(resp.encode('utf-8'))
            print(f"[TRACKER] Enviada lista de peers ativos para {client_address}: {resp}")

        elif command == "HEARTBEAT":
            ip = parts[1]
            port = parts[2]
            peer_key = f"{ip}:{port}"
            with PEERS_LOCK:
                peer_last_seen[peer_key] = time.time()
            #print(f"[TRACKER] Recebido heartbeat de {peer_key}")
            client_socket.sendall(b"OK")
        elif command == "UPDATE":
            ip = parts[1]
            port = parts[2]
            file_name = parts[3]
            
            peer_id = f"{ip}:{port}"

            with PEERS_LOCK:
                if peer_id in PEERS:
                    if file_name not in PEERS[peer_id]["files"]:
                        PEERS[peer_id]["files"].append(file_name)

                    client_socket.sendall(b"OK")
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
    # vamos definir a porta do tracker aqui
    start_tracker(host='127.0.0.1', port=5000)