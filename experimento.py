import time

def run_tests(peer, filename, peers_counts, runs=3):
    """
    peers_counts = [1, 2, 3, 4]
    """
    for n in peers_counts:
        print(f"\n=== TESTE COM {n} PEERS ===")

        # aqui você controla quantos peers estão ativos
        # ex: iniciando ou desligando peers manualmente
        # ou escolhendo apenas os n primeiros retornados pelo tracker

        for i in range(runs):
            print(f"[RUN {i+1}/{runs}]")
            peer.request_file(filename)
            time.sleep(1)
