#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>

#define MAX_FILES_PEER 10
#define FILENAME_LEN 100

typedef struct {
    char ip[32];
    int port;
    char files_shared[MAX_FILES_PEER][FILENAME_LEN];
    int file_count;
} Peer;

// Função para solicitar a lista de Pares do Tracker
void discover_peers(char* tracker_ip, int tracker_port, Peer *known_peers, int *known_count) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    
    // 1. Configurar o endereço do Tracker
    struct sockaddr_in tracker_addr;
    tracker_addr.sin_family = AF_INET;
    tracker_addr.sin_port = htons(tracker_port);
    inet_pton(AF_INET, tracker_ip, &tracker_addr.sin_addr);

    if (connect(sock, (struct sockaddr*)&tracker_addr, sizeof(tracker_addr)) < 0) {
        perror("[PEER] Erro ao conectar ao Tracker para descoberta");
        return;
    }

    // 2. Enviar o comando de Descoberta
    char* command = "GET_PEERS";
    send(sock, command, strlen(command), 0);
    
    // 3. Receber a lista de Pares
    char buffer[1024] = {0};
    ssize_t bytes_received = recv(sock, buffer, sizeof(buffer) - 1, 0);
    close(sock);

    if (bytes_received <= 0) {
        printf("[PEER] Nenhuma resposta do Tracker ou erro.\n");
        return;
    }

    // 4. Analisar (Parsear) a lista recebida
    printf("[PEER] Lista recebida: %s\n", buffer);
    
    // A lista vem no formato: "IP:PORTA,IP:PORTA,..."
    char* token = strtok(buffer, ",");
    int count = 0;
    
    while (token != NULL && count < 100) {
        char* colon = strchr(token, ':');
        
        if (colon) {
            *colon = '\0'; // Substitui ':' por '\0' para separar IP e Porta
            
            // Armazena no array local de Pares Conhecidos
            strcpy(known_peers[count].ip, token);
            known_peers[count].port = atoi(colon + 1);
            
            printf("  -> Descoberto: %s:%d\n", known_peers[count].ip, known_peers[count].port);
            count++;
        }
        token = strtok(NULL, ",");
    }
    
    *known_count = count;
}

// -------------------- THREAD DO SERVIDOR LOCAL DO PEER --------------------
//função peer_server transforma o seu Par em um servidor TCP capaz de receber conexões de outros Pares que foram descobertos através do Tracker.
// Essa função cria um socket TCP, vincula-o à porta especificada (my_port) e escuta por conexões de entrada.
void* peer_server(void* arg) {
    int my_port = *(int*)arg; // Porta onde o peer escutará (ficará acessível para outros pares na rede)

    int server_sock = socket(AF_INET, SOCK_STREAM, 0); // o socket atua como um ponto de comunicação para o servidor TCP

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(my_port);

    bind(server_sock, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_sock, 5);

    printf("[PEER] Servidor iniciado na porta %d\n", my_port);

    while (1) {
        int client = accept(server_sock, NULL, NULL);
        printf("[PEER] Conexão recebida de outro peer!\n");
        close(client);
    }

    return NULL;
}

// -------------------- MAIN DO PEER --------------------
int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Uso: %s <TRACKER_IP> <TRACKER_PORT> <MINHA_PORTA>\n", argv[0]);
        return 1;
    }

    char* tracker_ip = argv[1];
    int tracker_port = atoi(argv[2]);
    int my_port = atoi(argv[3]);

    // --------- REGISTRA NO TRACKER ---------
    int sock = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in tracker_addr;
    tracker_addr.sin_family = AF_INET;
    tracker_addr.sin_port = htons(tracker_port);
    inet_pton(AF_INET, tracker_ip, &tracker_addr.sin_addr);

    connect(sock, (struct sockaddr*)&tracker_addr, sizeof(tracker_addr));

    char msg[128];
    sprintf(msg, "REGISTER 127.0.0.1 %d", my_port);
    send(sock, msg, strlen(msg), 0);
    close(sock);

    printf("[PEER] Registrado no tracker!\n");

    // --------- INICIA THREAD DE SERVIDOR ---------
    pthread_t server_thread;
    pthread_create(&server_thread, NULL, peer_server, &my_port);
    pthread_detach(server_thread);

    // --------- DESCOBERTA DOS PARES CONHECIDOS ---------
    Peer known_peers[100]; // Array para armazenar pares descobertos
    int num_known_peers = 0;
    
    // Chama a nova função para obter a lista
    discover_peers(tracker_ip, tracker_port, known_peers, &num_known_peers);
    
    printf("[PEER] Total de pares descobertos: %d\n", num_known_peers);
    
    // **PRÓXIMO PASSO:** Usar 'known_peers' para iniciar conexões P2P!

    // --------- MANTÉM O PEER VIVO ---------
    while (1) {
        sleep(1);
    }

    return 0;
}
