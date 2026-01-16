import sys
import datetime
import matplotlib.pyplot as plt

consumer_latency_events = {}  # { group: { uid: [LatencyEvent] } }

class LatencyEvent:
    def __init__(self, insertion_date, latency, partition, offset, consumer_id):
        self.insertion_date = insertion_date
        self.latency = latency
        self.partition = partition
        self.offset = offset
        self.consumer_id = consumer_id


def get_global_time_bounds():
    all_dates = []

    for group in consumer_latency_events.values():
        for uid, events in group.items():
            for ev in events:
                all_dates.append(ev.insertion_date)

    if not all_dates:
        return None, None

    return min(all_dates), max(all_dates)


# -------------------------
# PARSING
# -------------------------

def parseLatency(line):
    global consumer_latency_events
    try:
        uid = line.split(" - ")[0]
        group = line.split(" - ")[1]
        date_str = line.split("insertion time is ")[1].split(",")[0]
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        latency = int(line.split("latency is ")[1].split(",")[0])
        partition = int(line.split("event come from partition ")[1].split(" ")[0])
        offset = int(line.split("and position ")[1].split(" ")[0])

        if group not in consumer_latency_events:
            consumer_latency_events[group] = {}

        if uid not in consumer_latency_events[group]:
            consumer_latency_events[group][uid] = []

        consumer_latency_events[group][uid].append(
            LatencyEvent(parsed_date, latency, partition, offset, uid)
        )

    except Exception as e:
        print(f"Error parsing latency: {e}, line: {line}")


def parseLine(line):
    if "insertion time is" in line:
        parseLatency(line)


def sort_all_events_by_timestamp():
    for group in consumer_latency_events:
        for uid in consumer_latency_events[group]:
            consumer_latency_events[group][uid] = sorted(
                consumer_latency_events[group][uid],
                key=lambda ev: ev.insertion_date
            )

# ----------------------------------------------
# 🌍 GLOBAL GRAPHS (TOUS GROUPES CONFONDUS)
# ----------------------------------------------

def plot_latency_by_partition_global(min_time, max_time):
    partitions = {}

    for group in consumer_latency_events.values():
        for uid, events in group.items():
            for ev in events:
                partitions.setdefault(ev.partition, {"dates": [], "latencies": []})
                partitions[ev.partition]["dates"].append(ev.insertion_date)
                partitions[ev.partition]["latencies"].append(ev.latency)

    plt.figure(figsize=(12, 6))
    for partition, data in partitions.items():
        plt.plot(data["dates"], data["latencies"], marker=".", linestyle="-", label=f"Partition {partition}")

    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")
    plt.title("GLOBAL — Latency over time per partition (all groups)")
    plt.grid(True)
    plt.legend()
    plt.xlim(min_time, max_time)
    plt.gcf().autofmt_xdate()

    plt.savefig("global_latency_by_partition.png")
    plt.close()
    print("➡️ Graphique généré : global_latency_by_partition.png")


def plot_latency_per_partition_global(min_time, max_time):
    partitions = {}

    for group in consumer_latency_events.values():
        for uid, events in group.items():
            for ev in events:
                partitions.setdefault(ev.partition, []).append(ev)

    for partition, events in partitions.items():
        events = sorted(events, key=lambda e: e.insertion_date)

        dates = [ev.insertion_date for ev in events]
        latencies = [ev.latency for ev in events]

        plt.figure(figsize=(12, 4))
        plt.plot(dates, latencies, marker="o", linestyle="-")

        plt.xlabel("Time")
        plt.ylabel("Latency (ms)")
        plt.title(f"GLOBAL — Latency over time – Partition {partition}")
        plt.grid(True)
        plt.xlim(min_time, max_time)
        plt.gcf().autofmt_xdate()

        filename = f"global_latency_partition_{partition}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")


# ----------------------------------------------
# 🧩 PER-GROUP GRAPHS
# ----------------------------------------------

def plot_latency_by_partition_per_group(min_time, max_time):
    for group, consumers in consumer_latency_events.items():
        partitions = {}

        for uid, events in consumers.items():
            for ev in events:
                partitions.setdefault(ev.partition, {"dates": [], "latencies": []})
                partitions[ev.partition]["dates"].append(ev.insertion_date)
                partitions[ev.partition]["latencies"].append(ev.latency)

        plt.figure(figsize=(12, 6))

        for partition, data in partitions.items():
            plt.plot(
                data["dates"],
                data["latencies"],
                marker=".",
                linestyle="-",
                label=f"Partition {partition}"
            )

        plt.xlabel("Time")
        plt.ylabel("Latency (ms)")
        plt.title(f"GROUP {group} — Latency over time per partition")
        plt.legend()
        plt.grid(True)

        plt.xlim(min_time, max_time)
        plt.gcf().autofmt_xdate()

        filename = f"group_{group}_latency_by_partition.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")


def plot_latency_per_partition_per_group(min_time, max_time):
    for group, consumers in consumer_latency_events.items():

        partitions = {}
        for uid, events in consumers.items():
            for ev in events:
                partitions.setdefault(ev.partition, []).append(ev)

        for partition, events in partitions.items():
            events = sorted(events, key=lambda e: e.insertion_date)

            dates = [ev.insertion_date for ev in events]
            latencies = [ev.latency for ev in events]

            plt.figure(figsize=(12, 4))
            plt.plot(dates, latencies, marker="o", linestyle="-")

            plt.xlabel("Time")
            plt.ylabel("Latency (ms)")
            plt.title(f"GROUP {group} — Latency over time – Partition {partition}")
            plt.grid(True)
            plt.xlim(min_time, max_time)
            plt.gcf().autofmt_xdate()

            filename = f"group_{group}_latency_partition_{partition}.png"
            plt.savefig(filename)
            plt.close()

            print(f"➡️ Graphique généré : {filename}")

def sort_all_events_by_timestamp():
    for group in consumer_latency_events:
        for uid in consumer_latency_events[group]:
            consumer_latency_events[group][uid] = sorted(
                consumer_latency_events[group][uid],
                key=lambda ev: ev.insertion_date
            )


# -------------------------------------------------
# 1️⃣ LATENCE PAR CONSOMMATEUR (tous les uids)
# -------------------------------------------------

def plot_latency_by_consumer(min_time, max_time):
    """
    Produit un graphe unique :
    - une courbe par consumer (peut être mélangé entre groupes)
    """

    plt.figure(figsize=(14, 7))

    for group, uids in consumer_latency_events.items():
        for uid, events in uids.items():
            dates = [ev.insertion_date for ev in events]
            lat = [ev.latency for ev in events]

            plt.plot(
                dates,
                lat,
                marker=".",
                linestyle="-",
                label=f"{group}:{uid}"
            )

    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")
    plt.title("Latency over time per consumer")
    plt.grid(True)
    plt.legend()
    plt.xlim(min_time, max_time)
    plt.gcf().autofmt_xdate()

    plt.savefig("latency_by_consumer.png")
    plt.close()

    print("➡️ Graphique généré : latency_by_consumer.png")


# -------------------------------------------------
# 2️⃣ LATENCE PAR GROUPE (un graphe par groupe)
# -------------------------------------------------
def plot_latency_by_group(min_time, max_time, latency_threshold=500):
    """
    Produit un graphe par groupe :
    - courbe de latence fusionnée de tous les consumers du groupe
    - courbe en escalier du nombre de consommateurs actifs (axe secondaire, échelle adaptée)
    - traits rouges pour les downscale, verts pour les upscale
    """
    for group, uids in consumer_latency_events.items():
        all_events = []
        for uid, events in uids.items():
            all_events.extend(events)
        all_events = sorted(all_events, key=lambda ev: ev.insertion_date)


        total_events = len(all_events)
        high_latency_events = [ev for ev in all_events if ev.latency >= latency_threshold]
        count_high = len(high_latency_events)
        percent_high = (count_high / total_events * 100) if total_events > 0 else 0

        uid_start_times = {}
        uid_end_times = {}
        for uid, events in uids.items():
            if events:
                uid_start_times[uid] = min(e.insertion_date for e in events)
                uid_end_times[uid] = max(e.insertion_date for e in events)

        all_change_times = []
        for uid, start in uid_start_times.items():
            all_change_times.append((start, 'start', uid))
        for uid, end in uid_end_times.items():
            all_change_times.append((end, 'end', uid))
        all_change_times.sort()

        active_uids = set()
        change_points = []
        for time, typ, uid in all_change_times:
            if typ == 'start':
                active_uids.add(uid)
            else:
                active_uids.discard(uid)
            change_points.append((time, len(active_uids)))

        dates = [ev.insertion_date for ev in all_events]
        latencies = [ev.latency for ev in all_events]

        step_times = [p[0] for p in change_points]
        step_counts = [p[1] for p in change_points]

        fig, ax1 = plt.subplots(figsize=(14, 6))

        color_latency = 'tab:blue'
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Latency (ms)", color=color_latency)
        ax1.plot(dates, latencies, marker=".", linestyle="-", color=color_latency, label='Latency')
        ax1.axhline(y=latency_threshold, color='red', linestyle='--')
        ax1.tick_params(axis='y', labelcolor=color_latency)
        ax1.grid(True)
        ax1.set_xlim(min_time, max_time)
        fig.autofmt_xdate()

        ax2 = ax1.twinx()
        color_consumers = 'tab:orange'
        ax2.set_ylabel("Number of consumers", color=color_consumers)
        ax2.step(step_times, step_counts, where='post', color=color_consumers, alpha=0.7, label='Active consumers', linewidth=2)
        ax2.tick_params(axis='y', labelcolor=color_consumers)

        min_consumers = min(step_counts) - 0.5
        max_consumers = max(step_counts) + 0.5
        ax2.set_ylim(min_consumers, max_consumers)

        # for i in range(1, len(change_points)):
        #     prev_count = change_points[i-1][1]
        #     curr_count = change_points[i][1]
        #     time = change_points[i][0]
        #     if curr_count > prev_count:
        #         ax1.axvline(x=time, color='green', linestyle='--', alpha=0.5, label='Upscale' if i == 1 else "")
        #     elif curr_count < prev_count:
        #         ax1.axvline(x=time, color='red', linestyle='--', alpha=0.5, label='Downscale' if i == 1 else "")


        text_str = f"Events > {latency_threshold}ms: {count_high} ({percent_high:.1f}%)"
        ax1.text(0.98, 0.98, text_str, transform=ax1.transAxes,
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Légende combinée
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title(f"Latency and Consumer Count over time — Group: {group}")
        fig.tight_layout()

        filename = f"latency_and_consumers_group_{group}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mtnd-consumer-analysis.py <file_log.txt>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, "r") as f:
        for line in f:
            parseLine(line)

    min_time, max_time = get_global_time_bounds()
    sort_all_events_by_timestamp()

    # 1. Latence par consommateur (global)
    plot_latency_by_consumer(min_time, max_time)

    # 2. Latence par groupe
    plot_latency_by_group(min_time, max_time)
    
#     # 🌍 Graphes globaux
#     plot_latency_by_partition_global(min_time, max_time)
#     plot_latency_per_partition_global(min_time, max_time)

#     # 🧩 Graphes par groupe
#     plot_latency_by_partition_per_group(min_time, max_time)
#     plot_latency_per_partition_per_group(min_time, max_time)

    print("➡️ Tous les graphes générés.")

if __name__ == "__main__":
    main()
