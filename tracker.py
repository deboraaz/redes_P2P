import socket
import threading
PEERS = {}
PEERS_LOCK = threading.Lock() #iniciada globalmente para evitar problemas de concorrencia

def handle_peer_conection(client_socket, client_address):
    try:
        #recebe os dados do peer
        data = client_socket.recv(1024).decode('utf-8').strip()
        print(f"[TRACKER] Conexão recebida de {client_address[0]}: {client_address[1]} : {data}")
    
        parts = data.split() #divide a string em partes
        command = parts[0] #comando recebido do peer

        if command == "REGISTER":
            peer_ip = parts[1]
            peer_port = int(parts[2])

            #ENTENDER/MODIFICAR
            files = parts[3].split(",") if len(parts) > 3 else []
            
            peer_address_key = f"{peer_ip}:{peer_port}"
            
            with PEERS_LOCK:
                if(peer_address_key not in PEERS):
                    PEERS[peer_address_key] = {"ip": peer_ip, "port": peer_port, "files": files}

                    print(f"[TRACKER] Peer registrado: {peer_address_key}")
                else:
                    print(f"[TRACKER] Peer já registrado: {peer_address_key} com arquivos atualizados {files}")
        elif command == "SEARCH":
            filename = parts[1]
            print(f"[TRACKER] Peer {client_address} está buscando pelo arquivo: {filename}")

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
            print(f"[TRACKER] Resposta enviada ao peer {client_address}: {responde}")

    except Exception as e:
        print(f"[TRACKER] Erro ao lidar com conexão do peer {client_address}: {e}")
    finally:
        client_socket.close()

def start_tracker(host='127.0.0.1', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"[TRACKER] Tracker iniciado em {host}:{port}. Aguardando conexões de peers...")

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