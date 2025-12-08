import sys
import datetime
import matplotlib.pyplot as plt

consumer_latency_events = {}

class LatencyEvent:
    def __init__(self, insertion_date, latency, partition, offset, consumer_id):
        self.insertion_date = insertion_date
        self.latency = latency
        self.partition = partition
        self.offset = offset
        self.consumer_id = consumer_id

def get_global_time_bounds():
    all_dates = []
    for uid, events in consumer_latency_events.items():
        for ev in events:
            all_dates.append(ev.insertion_date)

    if not all_dates:
        return None, None

    return min(all_dates), max(all_dates)


def parseLatency(line):
    global consumer_latency_events
    try:
        uid = line.split(" ")[0]
        date_str = line.split("insertion time is ")[1].split(",")[0]
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        latency = int(line.split("latency is ")[1].split(",")[0])
        partition = int(line.split("event come from partition ")[1].split(" ")[0])
        offset = int(line.split("and position ")[1].split(" ")[0])

        if uid not in consumer_latency_events:
            consumer_latency_events[uid] = []
        consumer_latency_events[uid].append(
            LatencyEvent(parsed_date, latency, partition, offset, uid)
        )

    except Exception as e:
        print(f"Error parsing latency: {e}, line: {line}")


def parseLine(line):
    if "insertion time is" in line:
        parseLatency(line)


def plot_offsets_by_partition(min_time, max_time):
    partitions = {}

    for uid, events in consumer_latency_events.items():
        for ev in events:
            if ev.partition not in partitions:
                partitions[ev.partition] = {"dates": [], "offsets": []}
            partitions[ev.partition]["dates"].append(ev.insertion_date)
            partitions[ev.partition]["offsets"].append(ev.offset)

    plt.figure(figsize=(12, 6))
    for partition, data in partitions.items():
        plt.plot(data["dates"], data["offsets"], marker=".", linestyle="-", label=f"Partition {partition}")

    plt.xlabel("Time")
    plt.ylabel("Offset")
    plt.title("Offsets over time per partition")
    plt.legend()
    plt.grid(True)

    plt.xlim(min_time, max_time)
    plt.gcf().autofmt_xdate()

    plt.savefig("offsets_by_partition.png")
    plt.close()

def plot_latency_by_consumer(min_time, max_time):
    plt.figure(figsize=(12, 6))

    for uid, events in consumer_latency_events.items():
        dates = [ev.insertion_date for ev in events]
        latencies = [ev.latency for ev in events]

        plt.plot(dates, latencies, marker=".", linestyle="-", label=f"Consumer {uid}")

    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")
    plt.title("Latency over time per consumer")
    plt.legend()
    plt.grid(True)

    plt.xlim(min_time, max_time)
    plt.gcf().autofmt_xdate()

    plt.savefig("latency_by_consumer.png")
    plt.close()


def plot_partition_assignments_per_consumer(min_time, max_time):
    for uid, events in consumer_latency_events.items():
        events = sorted(events, key=lambda e: e.insertion_date)

        dates = [ev.insertion_date for ev in events]
        partitions = [ev.partition for ev in events]

        plt.figure(figsize=(12, 4))
        plt.scatter(dates, partitions)

        plt.xlabel("Time")
        plt.ylabel("Partition")
        plt.title(f"Partition assignments over time – Consumer {uid}")
        plt.grid(True)

        # Applique les bornes globales
        plt.xlim(min_time, max_time)

        plt.gcf().autofmt_xdate()

        filename = f"partition_assignments_{uid}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")


def plot_latency_by_partition(min_time, max_time):
    partitions = {}

    # Regroupe les latences par partition
    for uid, events in consumer_latency_events.items():
        for ev in events:
            if ev.partition not in partitions:
                partitions[ev.partition] = {"dates": [], "latencies": []}
            partitions[ev.partition]["dates"].append(ev.insertion_date)
            partitions[ev.partition]["latencies"].append(ev.latency)

    plt.figure(figsize=(12, 6))

    # Une courbe par partition
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
    plt.title("Latency over time per partition")
    plt.legend()
    plt.grid(True)

    # Applique l’échelle temporelle globale
    if min_time and max_time:
        plt.xlim(min_time, max_time)

    plt.gcf().autofmt_xdate()
    plt.savefig("latency_by_partition.png")
    plt.close()

    print("➡️ Graphique généré : latency_by_partition.png")


def plot_latency_per_partition(min_time, max_time):
    # Regroupe les événements par partition
    partitions = {}

    for uid, events in consumer_latency_events.items():
        for ev in events:
            if ev.partition not in partitions:
                partitions[ev.partition] = []
            partitions[ev.partition].append(ev)

    # Pour chaque partition → un graphique
    for partition, events in partitions.items():

        # Trier par timestamp
        events = sorted(events, key=lambda e: e.insertion_date)

        dates = [ev.insertion_date for ev in events]
        latencies = [ev.latency for ev in events]

        plt.figure(figsize=(12, 4))
        plt.plot(dates, latencies, marker="o", linestyle="-")

        plt.xlabel("Time")
        plt.ylabel("Latency (ms)")
        plt.title(f"Latency over time – Partition {partition}")
        plt.grid(True)

        # Applique les bornes globales (communes à tous les graphiques)
        if min_time and max_time:
            plt.xlim(min_time, max_time)

        plt.gcf().autofmt_xdate()

        filename = f"latency_partition_{partition}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")



def sort_all_events_by_timestamp():
    for uid in consumer_latency_events:
        consumer_latency_events[uid] = sorted(
            consumer_latency_events[uid],
            key=lambda ev: ev.insertion_date
        )



def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_and_plot.py <file.log>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, "r") as f:
        for line in f:
            parseLine(line)
    min_time, max_time = get_global_time_bounds()
    sort_all_events_by_timestamp()

    plot_offsets_by_partition(min_time, max_time)
    plot_latency_by_consumer(min_time, max_time)
    plot_partition_assignments_per_consumer(min_time, max_time)
    plot_latency_by_partition(min_time, max_time)
    plot_latency_per_partition(min_time, max_time)
    

    print("➡️ Images générées : offsets_by_partition.png, latency_by_consumer.png")


if __name__ == "__main__":
    main()
