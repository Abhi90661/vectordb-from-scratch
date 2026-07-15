"""
backend/benchmarks/plot_results.py
====================================

Reads backend/benchmarks/results/results.csv and generates four bar
charts comparing the benchmarked index algorithms:

    - Build Time      -> build_time.png
    - Average Query Time -> query_time.png
    - Recall@K         -> recall.png
    - Memory Bytes      -> memory.png

Charts are saved to backend/benchmarks/graphs/.

Uses only the standard library `csv` module for reading data and
`matplotlib` for plotting.
"""

import csv
import os

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Paths (resolved relative to this file, so the script works regardless of
# the current working directory it's run from).
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV_PATH = os.path.join(_THIS_DIR, "results", "results.csv")
GRAPHS_DIR = os.path.join(_THIS_DIR, "graphs")

# (CSV column name, output filename, chart title, y-axis label)
_CHART_SPECS = [
    ("Build Time", "build_time.png", "Build Time by Algorithm", "Build Time (s)"),
    ("Average Query Time", "query_time.png", "Average Query Time by Algorithm", "Average Query Time (ms)"),
    ("Recall@K", "recall.png", "Recall@K by Algorithm", "Recall@K"),
    ("Memory Bytes", "memory.png", "Memory Usage by Algorithm", "Memory (Bytes)"),
]


def read_results(csv_path: str) -> list:
    """Read benchmark results from a CSV file into a list of dict rows."""
    with open(csv_path, "r", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def ensure_graphs_dir(graphs_dir: str) -> None:
    """Create the graphs output directory if it does not already exist."""
    os.makedirs(graphs_dir, exist_ok=True)


def plot_bar_chart(rows: list, column: str, filename: str, title: str, ylabel: str, graphs_dir: str) -> None:
    """Generate and save a single bar chart for one metric column."""
    algorithms = [row["Algorithm"] for row in rows]
    values = [float(row[column]) for row in rows]

    if column == "Average Query Time":
        values = [v * 1000 for v in values]

    fig, ax = plt.subplots(figsize=(8,5))
    ax.bar(algorithms, values)
    
    bars = ax.bar(algorithms, values)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_title(title)
    ax.set_xlabel("Algorithm")
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()

    output_path = os.path.join(graphs_dir, filename)
    fig.savefig(output_path)
    plt.close(fig)


def save_all_charts(rows: list, graphs_dir: str) -> None:
    """Generate all four benchmark comparison charts."""
    for column, filename, title, ylabel in _CHART_SPECS:
        plot_bar_chart(rows, column, filename, title, ylabel, graphs_dir)


def main() -> None:
    rows = read_results(RESULTS_CSV_PATH)
    ensure_graphs_dir(GRAPHS_DIR)
    save_all_charts(rows, GRAPHS_DIR)

    print("Saved:")
    for _, filename, _, _ in _CHART_SPECS:
        print(filename)


if __name__ == "__main__":
    main()