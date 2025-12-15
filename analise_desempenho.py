import csv
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt

CSV_FILE = "download_times.csv"

def load_data():
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append((
                r["arquivo"],
                int(r["tamanho"]),
                int(r["n_peers"]),
                float(r["tempo"])
            ))
    return rows

def aggregate(rows):
    times = defaultdict(list)

    for _, _, n_peers, tempo in rows:
        times[n_peers].append(tempo)

    peers = sorted(times.keys())
    means = [statistics.mean(times[p]) for p in peers]
    stds = [
        statistics.pstdev(times[p]) if len(times[p]) > 1 else 0
        for p in peers
    ]

    return peers, means, stds

def plot(peers, means, stds):
    x = range(len(peers))

    plt.figure()
    plt.bar(x, means, yerr=stds, capsize=5)
    plt.xticks(x, peers)

    plt.xlabel("Número de peers com o arquivo")
    plt.ylabel("Tempo médio de download (s)")
    plt.title("Desempenho do download P2P com chunks")
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig("grafico_desempenho.png", dpi=150)
    plt.show()

def main():
    rows = load_data()
    peers, means, stds = aggregate(rows)

    print("\nResumo:")
    for p, m, s in zip(peers, means, stds):
        print(f"{p} peers -> média {m:.2f}s | desvio {s:.2f}s")

    plot(peers, means, stds)

if __name__ == "__main__":
    main()
