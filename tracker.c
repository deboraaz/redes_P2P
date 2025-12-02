#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>

#define MAX_PEERS 100

// Estrutura de um peer
typedef struct {
    char ip[32];
    int port;
} Peer;

Peer peers[MAX_PEERS];
int peer_count = 0;

pthread_mutex_t lock;

// -------------------- THREAD QUE ATENDE CADA PEER --------------------
void* handle_peer(void* arg) {
    int client_sock = *(int*)arg;
    free(arg);

    char buffer[256];
    memset(buffer, 0, sizeof(buffer));

    read(client_sock, buffer, sizeof(buffer));

    // Exemplo esperado: "REGISTER 127.0.0.1 6002"
    char cmd[16], ip[32];
    int port;

    sscanf(buffer, "%s %s %d", cmd, ip, &port);

    if (strcmp(cmd, "REGISTER") == 0) {
        pthread_mutex_lock(&lock);

        peers[peer_count].port = port;
        strcpy(peers[peer_count].ip, ip);
        peer_count++;

        pthread_mutex_unlock(&lock);

        printf("[TRACKER] Novo peer registrado: %s:%d\n", ip, port);
    }else if(strcmp(cmd, "GET_PEERS") == 0){
        pthread_mutex_lock(&lock);

        char response_list[1024];
        memset(response_list, 0, sizeof(response_list)); // Limpa o buffer antes de usar
        for(int i = 0; i < peer_count; i++){
            char peer_info[64];
            sprintf(peer_info, "%s:%d\n", peers[i].ip, peers[i].port);
            strcat(response_list, peer_info);
        }

        pthread_mutex_unlock(&lock);

        send(client_sock, response_list, strlen(response_list), 0);
        printf("[TRACKER] Lista de pares enviada\n");
    }

    close(client_sock);
    return NULL;
}

// -------------------- MAIN DO TRACKER --------------------
int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Uso: %s <PORTA_TRACKER>\n", argv[0]);
        return 1;
    }

    int tracker_port = atoi(argv[1]);

    int server_sock = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(tracker_port);

    bind(server_sock, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_sock, 5);

    pthread_mutex_init(&lock, NULL);

    printf("[TRACKER] Rodando na porta %d...\n", tracker_port);

    while (1) {
        int *client_sock = malloc(sizeof(int));
        *client_sock = accept(server_sock, NULL, NULL);

        pthread_t t;
        pthread_create(&t, NULL, handle_peer, client_sock);
        pthread_detach(t);
    }

    return 0;
}
