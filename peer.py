import socket
import threading

# bibliotecas adicionadas para manipulação de arquivos
import os
from pathlib import Path # Importar Path para manipulação de caminhos
import sys # para pegar argumentos da linha de comando
import time #para o uso do heartbeat
import shutil #para manipulação de arquivos (foi usado shutil.copy para copia dos arquivos da pasta de exemplo para o peer)
import math
import queue
import csv

from desempenho import log_download

# informacoes do tracker (globais pra nao precisar ficar repetindo)
# TRACKER_IP = '127.0.0.1'
TRACKER_IP = '192.168.15.11'
TRACKER_PORT = 5000

TAM_CHUNK = 50 #tamanho pequeno pra testar com arquivos pequenos e ter pelo menos 3 chunks

#TAM_CHUNK = 4096 # tam dos chunks (blocos) do arquivo a serem enviados

class Peer:
    # Objeto: Representa um peer na rede P2P, capaz de se registrar com o tracker e obter a lista de outros peers
    #recebera o caminho dos arquivos na hora do cadastro

    def __init__(self, peer_ip: str, peer_port: int, data_dir_path: str):

        #informacoes dos dados do proprio peer
        self .peer_ip = peer_ip
        self.peer_port = peer_port

        # criacao do diretorio dos peers
        base_dir = Path("peers_data")
        base_dir.mkdir(exist_ok=True)

        # pasta individual de cada peer
        self.data_dir = base_dir / f"peer_{self.peer_port}"
        self.data_dir.mkdir(exist_ok=True)

        # copiar arquivos informados para a pasta do peer
        self.files = []
        for src_file in data_dir_path:
            src_path = Path(src_file)

            if src_path.exists():
                dest_path = self.data_dir / src_path.name
                shutil.copy(src_path, dest_path)
                self.files.append(str(dest_path))   # caminho completo do arquivo copiado
            else:
                print(f"[WARN] Arquivo não encontrado: {src_path}")
        
        # nomes dos arquivos
        self.processed_files = [Path(f).name for f in self.files]

        # dicionario para mapear nomes de arquivos aos seus caminhos completos
        # self.file_paths = {Path(f).name: f for f in self.files}
        self.file_paths = {}
        for f in self.files:
            name = os.path.basename(f)
            self.file_paths[name] = f

        #informacoes gerais da rede
        self.tracker_ip = TRACKER_IP
        self.tracker_port = TRACKER_PORT
        self.peers_list = [] #lista de pares na rede
        self.search_results = [] # armazena resultados da busca por arquivos

        self.server_thread = threading.Thread(target=self.file_server) #thread para o servidor de arquivos
        self.server_thread.daemon = True
        self.server_thread.start()

        self.hb_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.hb_thread.start()

        self.running = True

    def file_server(self):
        # Servidor para compartilhar arquivos com outros peers
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Permite reuso imediato da porta (evita TIME_WAIT)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        server_socket.bind((self.peer_ip, self.peer_port))
        server_socket.listen(5)

        #print(f"[PEER] Servidor de arquivos iniciado em {self.peer_ip}:{self.peer_port}. Aguardando conexões... ")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"[PEER] Conexão recebida do peer: {client_address}")

                handler_thread = threading.Thread(target=self.handle_file_request, args=(client_socket, client_address))
                handler_thread.start()
            except Exception as e:
                print(f"[PEER] Erro ao aceitar conexão: {e}")
        
    def handle_file_request(self, client_socket, client_address):
        # Lida com a requisição de arquivo de outro peer
        try:
            data = client_socket.recv(1024).decode('utf-8').strip()
            print(f"[PEER] Requisição recebida de {client_address}: {data}")

            parts = data.split()

            if parts[0] == "GET":
                filename = parts[1]
                offset = int(parts[2])
                size = int(parts[3])
                full_path = Path(self.file_paths[filename])

                if not full_path.exists():
                    response = "ERROR: Arquivo não encontrado"
                    client_socket.sendall(response.encode('utf-8'))
                    return
                
                #dicionario para mapear nomes de arquivos aos seus caminhos completos
                # arquivo solicitado
                if filename not in self.file_paths:
                    response = "ERROR: Arquivo não encontrado"
                    client_socket.sendall(response.encode('utf-8'))
                    return

                full_path = self.file_paths[filename]

                if size == 0:
                    file_size = os.path.getsize(full_path)
                    client_socket.sendall(str(file_size).encode('utf-8'))
                    return

                with open(full_path, "rb") as f:
                    f.seek(offset)
                    chunk = f.read(size)
                    client_socket.sendall(chunk)
                    print(f"[PEER] Enviado chunk offset={offset} size={size} para {client_address}")

                print(f"[PEER] Enviado arquivo {filename} para {client_address}")
                    
        except Exception as e:
            print(f"[PEER] Erro ao lidar com requisição de {client_address}: {e}")
        finally:
            client_socket.close()

    def download_file(self, file_name, peer_ip, peer_port):

        inicio = time.time()

        peers = self.search_results[:]  # lista de peers que têm o arquivo
        if not peers:
            print("[PEER] Nenhum peer disponível para baixar.")
            return

        # 1 — Descobrir tamanho do arquivo (primeiro peer)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, peer_port))
            sock.sendall(f"GET {file_name} 0 0".encode())
            size = int(sock.recv(32).decode())
            sock.close()
        except:
            print("[PEER] Erro ao obter tamanho do arquivo.")
            return

        num_chunks = math.ceil(size / TAM_CHUNK)
        print(f"[PEER] Arquivo tem {size} bytes. Dividido em {num_chunks} chunks.")

        # 2 — Criar buffer final
        final_data = [None] * num_chunks

        # 3 — Fila de chunks
        q = queue.Queue()
        for i in range(num_chunks):
            q.put(i)

        # 4 — Worker de download
        def worker(peer_addr):
            ip, port = peer_addr.split(":")
            port = int(port)

            while not q.empty():
                try:
                    # 
                    idx = q.get_nowait()
                except:
                    return

                offset = idx * TAM_CHUNK
                size_request = TAM_CHUNK

                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((ip, port))
                    s.sendall(f"GET {file_name} {offset} {size_request}".encode())
                    data = s.recv(size_request)
                    s.close()

                    final_data[idx] = data
                    print(f"[CHUNK] Recebido chunk {idx} de {ip}:{port}")

                except Exception as e:
                    print(f"[ERRO] Falha ao baixar chunk {idx} de {ip}:{port}: {e}")
                    q.put(idx)  # devolve o chunk pra fila

        # 5 — Criar threads (1 por peer)
        threads = []
        for peer_addr in peers:
            t = threading.Thread(target=worker, args=(peer_addr,))
            t.start()
            threads.append(t)

        # 6 — Esperar threads terminarem
        for t in threads:
            t.join()

        # 7 — Reconstruir arquivo
        save_path = self.data_dir / file_name # salvar na pasta do peer
        with open(save_path, "wb") as f:
            for chunk in final_data:
                if chunk:
                    f.write(chunk)

        print(f"[PEER] Download completo: {file_name}")

        fim = time.time()
        tempo_total = fim - inicio

        tamanho = os.path.getsize(save_path)
        n_peers = len(self.search_results)

        log_download(file_name, tamanho, n_peers, tempo_total)

        # atualizar o dicionario de caminhos de arquivos
        self.file_paths[file_name] = str(save_path)

        # Avisar ao tracker que agora possui o arquivo
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.tracker_ip, self.tracker_port))
                sock.sendall(f"UPDATE {self.peer_ip} {self.peer_port} {file_name}".encode())
        except Exception as e:
            print("[PEER] Falha ao atualizar o tracker:", e)


    def request_file_peers(self, file_name):
        print(f"[PEER] Requisitando lista de peers que possuem o arquivo: {file_name}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.tracker_ip, self.tracker_port))
                
                request_command = f"SEARCH {file_name}"
                sock.sendall(request_command.encode('utf-8'))

                # Recebe a resposta do tracker
                resp = sock.recv(1024).decode('utf-8').strip()
                print(f"[Tracker -> PEER] Resposta: {resp}")

                # Salva os peers que possuem o arquivo (sera usado depois para baixar o arquivo)
                if resp != "NAO ENCONTRADO":
                    self.search_results = resp.split(",")
                else:
                    self.search_results = []

        except Exception as e:
            print(f"[PEER] Erro ao solicitar arquivo do tracker: {resp}")

    # funcao que processa os comandos do usuario
    def handle_command(self, command):
        parts = command.split()

        if parts[0] == "exit":
            # envia UNREGISTER ao tracker para remoção imediata (saída limpa)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self.tracker_ip, self.tracker_port))
                    sock.sendall(f"UNREGISTER {self.peer_ip} {self.peer_port}".encode())
            except Exception:
                pass

            self.running = False # usado pra parar o loop em command_listener
            print("[PEER] Desligando o peer.")
            sys.exit(0)
        
        elif parts[0] == "list":
            # Solicita ao tracker a lista atual de peers ativos
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self.tracker_ip, self.tracker_port))
                    sock.sendall("LIST".encode())
                    resp = sock.recv(4096).decode().strip() #decode converte bytes em texto e strip remove espacos e quebras de linha
            except Exception as e:
                print("[PEER] Erro ao pedir lista ao tracker:", e)
                resp = ""

            if resp:
                self.peers_list = resp.split(",")
            else:
                self.peers_list = []

            print("[PEER] Lista de peers registrados (atual):")
            for peer in self.peers_list:
                print(f" - {peer}")
                
        elif parts[0] == "search":
            # Busca por arquivos na rede
            if len(parts) < 2:
                print("[PEER] Uso: search <file_name>")
                return
            
            file_name = parts[1]
            print(f"[PEER] Buscando por arquivos: {file_name}")
            
            self.request_file_peers(file_name)
        elif parts[0] == "download":
            if len(parts) < 2:
                print("[PEER] Uso: download <file_name>")
                return

            file_name = parts[1]

            # Verifica se já existe resultado de busca
            if not hasattr(self, "search_results") or len(self.search_results) == 0:
                print("[PEER] Nenhum resultado de busca. Use 'search <arquivo>' antes.")
                return

            # Pega o primeiro peer que tem o arquivo
            target = self.search_results[0]
            target_ip, target_port = target.split(":")

            print(f"[PEER] Baixando {file_name} de {target_ip}:{target_port} ...")

            self.download_file(file_name, target_ip, int(target_port))
            return

        else:
            print(f"[PEER] Comando desconhecido: {command}")

    # metodo para escutar comandos do usuario
    def command_listener(self):
        print("[PEER] Comandos disponiveis: list | search <file_name> | download <file_name> | exit")

        while self.running:
            try:
                user_input = input("> ").strip()

                if user_input == "":
                    continue

                self.handle_command(user_input)
            
            except EOFError:
                print("[PEER] Entrada de dados encerrada.")
                self.running = False
            except KeyboardInterrupt:
                print("\n[PEER] Interrompido pelo usuário.")
                self.running = False

    # thread para enviar heartbeats ao tracker periodicamente - 10 seg - (pra confirmar que esta ativo na rede)
    def heartbeat_loop(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self.tracker_ip, self.tracker_port)) # conexao unica, usada apenas para enviar heartbeat (a cada x seg)
                    sock.sendall(f"HEARTBEAT {self.peer_ip} {self.peer_port}".encode())
            except Exception:
                pass
            time.sleep(10) # envia heartbeat a cada 10 segundos

    # Conecta ao tracker para registrar o peer
    def connect_to_tracker(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.tracker_ip, self.tracker_port)) # conexao unica, usada apenas para iniciar o peer
                
                # Registra o peer no tracker
                files_str = ",".join(self.processed_files)
                register_command = f"REGISTER {self.peer_ip} {self.peer_port} {files_str}"
                sock.sendall(register_command.encode('utf-8'))
                print(f"[PEER] Registrado no tracker")

                # Inicia a thread de heartbeat
                hb_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
                hb_thread.start()

        except Exception as e:
            print(f"[PEER] Erro ao conectar ao tracker: {e}")

if __name__ == "__main__":
    # verificando se os argumentos foram passados corretamente
    if len(sys.argv) < 4:
        print("ERRO: Uso correto: python3 peer.py <PEER_IP> <PEER_PORT> <DATA_DIR_PATH>")
        sys.exit(1)

    try:
        peer_ip = sys.argv[1]
        peer_port = int(sys.argv[2])

        # arquivos começam no argumento 3 em diante
        file_paths = sys.argv[3:]

        peer = Peer(peer_ip, peer_port, file_paths)
        peer.connect_to_tracker()

        # Inicia a thread para escutar comandos do usuário
        t = threading.Thread(target=peer.command_listener)
        t.daemon = False # permite que o programa principal continue rodando
        t.start()

    except ValueError:
        print("ERRO: A porta do peer deve ser um número inteiro.")
        sys.exit(1)