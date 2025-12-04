# setup_files.py é utilizado para configurar os diretórios dos peers (atribuição de arquivos)

#para os arquivos
import os
from pathlib import Path
import shutil #para manipulação de arquivos (foi usado shutil.copy para copia dos arquivos da pasta de exemplo para o peer)

#pasta onde estao os arquivos de exemplo
example_files_dir = Path("arquivos")

def setup_peer_directories(peer_configs):
    # Cria diretórios para cada peer e copia os arquivos de exemplo
    base_dir = Path("peers_data")
    base_dir.mkdir(exist_ok=True) #cria a pasta principal peer_data

    if not example_files_dir.exists():
        print(f"[SETUP] Diretório de arquivos de exemplo não encontrado: {example_files_dir}")
        return
    for port, file_names in peer_configs.items():
        peer_dir = base_dir / f"peer_{port}"
        peer_dir.mkdir(exist_ok=True) #cria a pasta do peer

        print(f"[SETUP] Configurando diretório para Peer na porta {port} com arquivos: {file_names}")

        for file_name in file_names:
            src_file = example_files_dir / Path(file_name).name
            dest_file = peer_dir / Path(file_name).name

            if src_file.exists():
                shutil.copy(src_file, dest_file)
                print(f"[SETUP] Copiado {src_file} para {dest_file}")
            else:
                print(f"[SETUP] Arquivo de exemplo não encontrado: {src_file}")

if __name__ == "__main__":
    # Dicionario peer_configs: porta do peer e arquivos que ele possui
    # 4 arquivos - cada um esta em 3 peers diferentes
    peer_configs = {
        6001: ["arq1.txt", "arq2.txt", "arq3.txt"],
        6002: ["arq2.txt", "arq3.txt", "arq4.txt"],
        6003: ["arq3.txt", "arq4.txt", "arq1.txt"],
        6004: ["arq1.txt", "arq2.txt", "arq3.txt"],
    }

    setup_peer_directories(peer_configs)