import socket
import threading

# bibliotecas adicionadas para manipulação de arquivos
import os
import json # Necessário para enviar dados estruturados ao tracker (se você for usar o modelo JSON)
from pathlib import Path # Importar Path para manipulação de caminhos

import sys # para pegar argumentos da linha de comando

# informacoes do tracker (globais pra nao precisar ficar repetindo)
TRACKER_IP = '127.0.0.1'
TRACKER_PORT = 5000

class Peer:
    # Objeto: Representa um peer na rede P2P, capaz de se registrar com o tracker e obter a lista de outros peers
    #recebera o caminho dos arquivos na hora do cadastro

    def __init__(self, peer_ip: str, peer_port: int, data_dir_path: str):
        #informacoes gerais da rede
        self.tracker_ip = TRACKER_IP
        self.tracker_port = TRACKER_PORT
        self.peers_list = [] #lista de pares na rede

        #informacoes dos dados do proprio peer
        self.peer_ip = peer_ip
        self.peer_port = peer_port

        self.data_dir = Path(data_dir_path)
        # lista de arquivos que o peer possui
        self.processed_files = [f.name for f in self.data_dir.iterdir() if f.is_file()]
        print("[PEER]: IP {} : Porta {} : Arquivos {}".format(self.peer_ip, self.peer_port, self.processed_files))

        # flag para desligar o peer quando o usuário digitar "exit"
        self.running = True

    def connect_to_tracker(self):
        # Conecta ao tracker para registrar o peer

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.tracker_ip, self.tracker_port))
                
                # Registra o peer no tracker
                files_str = ",".join(self.processed_files)
                register_command = f"REGISTER {self.peer_ip} {self.peer_port} {files_str}"
                sock.sendall(register_command.encode('utf-8'))
                print(f"[PEER] Registrado no tracker: {register_command}")

        except Exception as e:
            print(f"[PEER] Erro ao conectar ao tracker: {e}")

    # metodo para escutar comandos do usuario
    def command_listener(self):
        print("[PEER] Pronto para receber comandos.")

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

    # funcao que processa os comandos do usuario
    def handle_command(self, command):
        parts = command.split()

        if parts[0] == "exit":
            self.running = False
            print("[PEER] Desligando o peer.")
            sys.exit(0)
        elif parts[0] == "list":
            # Lista os peers registrados no tracker
            print("[PEER] Lista de peers registrados:")
            for peer in self.peers_list:
                print(f" - {peer}")
        elif parts[0] == "search":
            if len(parts) < 2:
                print("[PEER] Uso: search <file_name>")
                return
            
            file_name = parts[1]
            print(f"[PEER] Buscando por arquivos: {file_name}")
            
            self.request_file_peers(file_name)
        else:
            print(f"[PEER] Comando desconhecido: {command}")

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

                # Aqui você pode processar a resposta e atualizar a lista de peers
                #self.peers_list = resp.split(",") if resp else []
        except Exception as e:
            print(f"[PEER] Erro ao solicitar arquivo do tracker: {resp}")

if __name__ == "__main__":
    # verificando se os argumentos foram passados corretamente
    if len(sys.argv) != 4:
        print("ERRO: Uso correto: python3 peer.py <PEER_IP> <PEER_PORT> <DATA_DIR_PATH>")
        sys.exit(1)

    try:
        peer_ip = sys.argv[1]
        peer_port = int(sys.argv[2])
        data_dir_path = sys.argv[3]

        peer = Peer(peer_ip, peer_port, data_dir_path)
        peer.connect_to_tracker()

        # Inicia a thread para escutar comandos do usuário
        t = threading.Thread(target=peer.command_listener)
        t.daemon = False # permite que o programa principal continue rodando
        t.start()

    except ValueError:
        print("ERRO: A porta do peer deve ser um número inteiro.")
        sys.exit(1)