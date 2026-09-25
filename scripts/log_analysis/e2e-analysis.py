import sys
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

X_SMALL_SIZE = 10
SMALL_SIZE = 14
MEDIUM_SIZE = 20
BIGGER_SIZE = 26

plt.rc('font', size=SMALL_SIZE)
plt.rc('axes', titlesize=SMALL_SIZE)
plt.rc('axes', labelsize=SMALL_SIZE)
plt.rc('xtick', labelsize=SMALL_SIZE)
plt.rc('ytick', labelsize=SMALL_SIZE)
plt.rc('legend', fontsize=SMALL_SIZE)

def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def load_json_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_end_to_end_metrics(trackers):
    finish_times = []
    durations = []

    for tracker in trackers:
        events = tracker.get("events") or []
        if not events:
            continue

        timestamps = [parse_timestamp(e["timestamp"]) for e in events]
        duration = tracker.get("endToEndDurationMs")
        if duration in (None, 0) and len(timestamps) > 1:
            duration = int((max(timestamps) - min(timestamps)).total_seconds() * 1000)

        finish_times.append(max(timestamps))
        durations.append(duration)

    return finish_times, durations

def generate_end_to_end_latency_plot(finish_times, durations, total_events):
    plt.figure(figsize=(16, 6))
    color = "#5C669F"

    plt.scatter(finish_times, durations, alpha=0.3, s=5, color=color)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xlabel("Heure de fin")
    plt.ylabel("Durée end-to-end (ms)")
    plt.title("Durée end-to-end par événement")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    plt.text(
        0.99,
        0.98,
        f"total events: {total_events}",
        transform=plt.gca().transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        fontsize=13,
    )

    plt.tight_layout()
    plt.savefig("e2e_latency.png", dpi=300, bbox_inches="tight", transparent=True)
    plt.close()

def generate_end_to_end_percentile_plot(durations):
    plt.figure(figsize=(16, 6))
    sorted_durations = np.sort(np.asarray(durations, dtype=float))
    cumulative_counts = np.arange(1, len(sorted_durations) + 1)

    plt.plot(sorted_durations, cumulative_counts)
    plt.xlabel("Durée end-to-end (ms)")
    plt.ylabel("Nombre cumulé d'événements")
    plt.title("Courbe cumulative des événements par durée")
    plt.grid(True, alpha=0.3)

    if len(sorted_durations) > 0:
        for percentile in [50, 90, 95, 99]:
            p = np.percentile(sorted_durations, percentile)
            plt.axvline(p, color="r", linestyle="--", alpha=0.7, label=f"{percentile}th percentile")
        plt.legend()

    plt.tight_layout()
    plt.savefig("e2e_percentile_distribution.png", dpi=300, bbox_inches="tight")
    plt.close()

def build_latency_by_node_origin(trackers):
    latency_points_by_node = {}

    for tracker in trackers:
        for event in tracker.get("events") or []:
            node_origin = event.get("nodeOrigin", "unknown")
            timestamp = parse_timestamp(event["timestamp"])
            latency = float(event.get("latency", 0))

            latency_points_by_node.setdefault(node_origin, []).append((timestamp, latency))

    return latency_points_by_node

def generate_latency_per_node_origin_plot(latency_points_by_node):
    if not latency_points_by_node:
        return

    plt.figure(figsize=(16, 8))
    ax = plt.gca()

    for node_origin, points in sorted(latency_points_by_node.items()):
        timestamps = [ts for ts, _ in points]
        latencies = [lat for _, lat in points]
        
        points.sort(key=lambda item: item[0])

        ax.plot(
            timestamps,
            latencies,
            marker=".",
            linestyle="-",
            linewidth=1.5,
            alpha=0.8,
            label=node_origin,
        )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.set_xlabel("Time")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Latency per nodeOrigin over time")
    ax.grid(True, alpha=0.3)
    ax.legend(title="nodeOrigin", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig("latency_per_node_origin.png", dpi=300, bbox_inches="tight")
    plt.close()

def generate_individual_latency_plots(latency_points_by_node, latency_threshold = 700):
    for node_origin, points in latency_points_by_node.items():
        plt.figure(figsize=(16, 5))
        ax = plt.gca()
        timestamps = [ts for ts, _ in points]
        latencies = [lat for _, lat in points]

        total_events = len(latencies)
        high_latency_events = [ev for ev in latencies if ev >= latency_threshold]
        count_high = len(high_latency_events)
        percent_high = (count_high / total_events * 100) if total_events > 0 else 0

        
        points.sort(key=lambda item: item[0])

        plt.plot(
            timestamps,
            latencies,
            marker=".",
            linestyle="-",
            linewidth=1.5,
            color="#5C669F",
            alpha=0.5
        )
        plt.axhline(y=latency_threshold, color='red', linestyle='--')
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.set_xlabel("Time")
        ax.set_ylabel("Latency (ms)")
        ax.set_title(f"Latency for {node_origin}")
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        safe_name = node_origin.replace(" ", "_").replace("/", "_")

        text_str = f"Events > {latency_threshold}ms: {count_high} ({percent_high:.1f}%)"
        ax.text(0.98, 0.98, text_str, transform=ax.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        text_total_events = f"total events: {total_events}"
        ax.text(0.98, 0, text_total_events, transform=ax.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontsize=13)

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        ax.set_title(f"Latency and Consumer Count over time — Group: {safe_name}")
        plt.tight_layout()

        plt.savefig(f"latency_{safe_name}.png", dpi=300, bbox_inches="tight")
        plt.close()

def print_trackers_without_4_events(trackers):
    total_not_4_events = sum(1 for tracker in trackers if len(tracker.get("events") or []) != 4)
    print(f"Total trackers without 4 events: {total_not_4_events}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 e2e-analysis.py <e2e-analyzer.json>")
        sys.exit(1)

    input_file = sys.argv[1]

    data = load_json_data(input_file)
    trackers = data.get("data", [])

    print_trackers_without_4_events(trackers)
    finish_times, durations = get_end_to_end_metrics(trackers)
    total_events = int(data.get("metadata", {}).get("count", len(durations)))

    generate_end_to_end_latency_plot(finish_times, durations, total_events)
    generate_end_to_end_percentile_plot(durations)

    latency_points_by_node = build_latency_by_node_origin(trackers)
    generate_latency_per_node_origin_plot(latency_points_by_node)
    generate_individual_latency_plots(latency_points_by_node)

if __name__ == "__main__":
    main()