import sys
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Dict
import re
from datetime import datetime, timedelta
import json
from collections import defaultdict
import numpy as np

X_SMALL_SIZE = 10
SMALL_SIZE = 14
MEDIUM_SIZE = 20
BIGGER_SIZE = 26

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=SMALL_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
# plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

# ============================================
# CLASSES
# ============================================

class Partition:
    def __init__(self, id, lag=0, arrivalRate={}, processingTime=0.0, processingCount=0.0, latency=0.0, lagRebalancing=0.0):
        self.id = id
        self.lag = lag
        self.arrivalRate = arrivalRate
        self.processingTime = processingTime
        self.processingCount = processingCount
        self.latency = latency
        self.lagRebalancing = lagRebalancing

class Consumer:
    def __init__(self, id, assignedPartitions, dynamicProcessingCapacity=0.0):
        self.id = id
        self.assignedPartitions = assignedPartitions
        self.dynamicProcessingCapacity = dynamicProcessingCapacity

class ConsumerGroup:
    def __init__(self, wsla, inputTopic, consumerName, kafkaGroupName, processingRateFallBack, topicPartitions, lastUpScaleDecision, assignment, fup, fdown, name, groupName, upProcessRate, downProcessRate, upLagCapacity, downLagCapacity):
        self.wsla = wsla
        self.inputTopic = inputTopic
        self.consumerName = consumerName
        self.kafkaGroupName = kafkaGroupName
        self.processingRateFallBack = processingRateFallBack
        self.topicPartitions = topicPartitions
        self.lastUpScaleDecision = datetime.strptime(lastUpScaleDecision, '%m/%d/%YT%H:%M:%S.%f') if lastUpScaleDecision != "N/A" else None
        self.assignment = assignment
        self.fup = fup
        self.fdown = fdown
        self.name = name
        self.groupName = groupName
        self.upProcessRate = upProcessRate
        self.downProcessRate = downProcessRate
        self.upLagCapacity = upLagCapacity
        self.downLagCapacity = downLagCapacity

class PrometheusData:
    def __init__(self, timestamp, consumerGroup, partitionsMetaData, consumersMetaData, parentArrivalRate, totalArrivalRate, totalExternalArrivalRate, avgParentArrivalRate):
        self.timestamp = timestamp
        self.consumerGroup = consumerGroup
        self.partitionsMetaData = partitionsMetaData
        self.consumersMetaData = consumersMetaData
        self.parentArrivalRate = parentArrivalRate
        self.totalArrivalRate = totalArrivalRate
        self.totalExternalArrivalRate = totalExternalArrivalRate
        self.avgParentArrivalRate = avgParentArrivalRate

class LatencyEvent:
    def __init__(self, insertion_date, latency, partition, offset, consumer_id, proces_time):
        self.insertion_date = insertion_date
        self.latency = latency
        self.partition = partition
        self.offset = offset
        self.consumer_id = consumer_id
        self.proces_time = proces_time

# ============================================
# GLOBAL VARIABLES
# ============================================

consumer_latency_events = {}  # { group: { uid: [LatencyEvent] } }

# ============================================
# PARSING FUNCTIONS
# ============================================

def pulled_data_from_prometheus(line):
    # Extraction du timestamp de la ligne de log
    log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
    log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')

    # Extraction de la partie JSON
    data = line.split("Pulled data from Prometheus :")[1]
    json_start = data.find('[')
    json_end = data.rfind(']')
    json_str = data[json_start:json_end+1]
    json_str = json_str.replace("\\", "\"")
    data_list = json.loads(json_str)

    
    prometheus_data_list = []
    for data in data_list:
        # Parsing des partitions
        partitions = {}
        for partition_key, partition_data in data["partitionsMetaData"].items():
            partition_id = partition_data["partition"]["id"]
            partitions[partition_id] = Partition(
                id=partition_id,
                lag=partition_data["lag"],
                arrivalRate=partition_data["arrivalRate"],
                processingTime=partition_data["processingTime"],
                processingCount=partition_data["processingCount"],
                latency=partition_data["latency"],
                lagRebalancing=partition_data["lagRebalancing"]
            )

        # Parsing des consumers
        consumers = {}
        for consumer_key, consumer_data in data["consumersMetaData"].items():
            consumer_id = consumer_data["consumer"]["id"]
            assigned_partitions = [p["id"] for p in consumer_data["consumer"]["assignedPartitions"]]
            consumers[consumer_id] = Consumer(
                id=consumer_id,
                assignedPartitions=assigned_partitions,
                dynamicProcessingCapacity=consumer_data["dynamicProcessingCapacity"]
            )

        # Parsing du consumerGroup
        topic_partitions = [p["id"] for p in data["consumerGroup"]["topicPartitions"]]
        assignment = [a for a in data["consumerGroup"]["assignment"]]

        consumer_group = ConsumerGroup(
            wsla=data["consumerGroup"]["wsla"],
            inputTopic=data["consumerGroup"]["inputTopic"],
            consumerName=data["consumerGroup"]["consumerName"],
            kafkaGroupName=data["consumerGroup"]["kafkaGroupName"],
            processingRateFallBack=data["consumerGroup"]["processingRateFallBack"],
            topicPartitions=topic_partitions,
            lastUpScaleDecision=data["consumerGroup"]["lastUpScaleDecision"],
            assignment=assignment,
            fup=data["consumerGroup"]["fup"],
            fdown=data["consumerGroup"]["fdown"],
            name=data["consumerGroup"]["name"],
            groupName=data["consumerGroup"]["groupName"],
            upProcessRate = data["consumerGroup"]["fup"] * len(assignment) * 200,
            downProcessRate = data["consumerGroup"]["fdown"] * len(assignment) * 200,
            upLagCapacity =  data["consumerGroup"]["fup"] * len(assignment) * 200 * 0.5,
            downLagCapacity = data["consumerGroup"]["fdown"] * len(assignment) * 0.5
        )

        # Création de l'objet PrometheusData
        prometheus_data = PrometheusData(
            timestamp=log_timestamp,
            consumerGroup=consumer_group,
            partitionsMetaData=partitions,
            consumersMetaData=consumers,
            parentArrivalRate=data["parentArrivalRate"],
            totalArrivalRate=data["totalInputArrivalRate"],
            totalExternalArrivalRate=data["totalExternalArrivalRate"],
            avgParentArrivalRate=data["avgParentArrivalRate"]
        )
        prometheus_data_list.append(prometheus_data)

    return prometheus_data_list

def pulled_data_from_prometheus_for_nb_consumer(line):
    # Extraction du timestamp de la ligne de log
    log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
    log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')

    # Extraction de la partie JSON
    data = line.split("Pulled data from Prometheus :")[1]
    json_start = data.find('[')
    json_end = data.rfind(']')
    json_str = data[json_start:json_end+1]
    json_str = json_str.replace("\\", "\"")
    data_list = json.loads(json_str)

    
    prometheus_data_list = []
    
    for data in data_list:
        res = {}
        res["timestamp"] = log_timestamp
        res["name"] = data["consumerGroup"]["consumerName"]
        res["consumer"] = len(data["consumerGroup"]["assignment"])
        prometheus_data_list.append(res)
    return prometheus_data_list


def parseLatency(line):
    global consumer_latency_events
    try:
        uid = line.split(" - ")[0]
        group = line.split(" - ")[1]
        date_str = line.split("insertion time is ")[1].split(",")[0]
        parsed_date = datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        latency = int(line.split("latency is ")[1].split(",")[0])
        partition = int(line.split("event come from partition ")[1].split(" ")[0])
        offset = int(line.split("and position ")[1].split(" ")[0])
        process_time = float(line.split("time for process ")[1].split(" ")[0])
        event_provider = line.split("and it is from node ")[1].split(" ")[0]

        if group not in consumer_latency_events:
            consumer_latency_events[group] = {}

        if uid not in consumer_latency_events[group]:
            consumer_latency_events[group][uid] = []

        consumer_latency_events[group][uid].append(
            LatencyEvent(parsed_date, latency, partition, offset, uid, process_time)
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

def get_global_time_bounds():
    all_dates = []

    for group in consumer_latency_events.values():
        for uid, events in group.items():
            for ev in events:
                all_dates.append(ev.insertion_date)

    if not all_dates:
        return None, None

    return min(all_dates), max(all_dates)

# ============================================
# CONTROLLER PLOTTING FUNCTIONS
# ============================================

def plot_group_arrival_rate(grouped_data):
    for group_name, data_list in grouped_data.items():
        timestamps = [data.timestamp for data in data_list]
        nb_consumers = [len(data.consumerGroup.assignment) for data in data_list]
        avg_total_arrival_rates_by_nb_assignment = []
        for data in data_list:
            avg_total_arrival_rates_by_nb_assignment.append(data.totalArrivalRate / len(data.consumerGroup.assignment) if len(data.consumerGroup.assignment) > 0 else 0)

        fig, ax1 = plt.subplots(figsize=(14, 7))
        color_arrival = 'tab:orange'
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Avg Total Arrival Rate per Consumer', color=color_arrival)
        ax1.axhline(y=(data.consumerGroup.fup * 200), color='red', linestyle='--', label='Up Process Rate')
        ax1.axhline(y=(data.consumerGroup.fdown * 200), color='red', linestyle='--', label='Down Process Rate')
        ax1.plot(timestamps, avg_total_arrival_rates_by_nb_assignment, color=color_arrival, marker='x', label='Avg Total Arrival Rate per Consumer')
        ax1.tick_params(axis='y', labelcolor=color_arrival)
        ax1.grid(True)
        ax2 = ax1.twinx()
        color_consumers = 'tab:green'
        ax2.set_ylabel('Number of Consumers', color=color_consumers)
        ax2.step(timestamps, nb_consumers, color=color_consumers, label='Number of Consumers', alpha=.05)
        ax2.fill_between(timestamps, nb_consumers, color=color_consumers, step="pre", alpha=0.05)
        ax2.tick_params(axis='y', labelcolor=color_consumers)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.title(f"Avg Total Arrival Rate per Consumer over Time — Consumer Group: {group_name}")
        fig.tight_layout()
        filename = f"avg_total_arrival_rate_per_consumer_group_{group_name}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

def plot_group_lag(grouped_data):
    for group_name, data_list in grouped_data.items():
        timestamps = [data.timestamp for data in data_list]
        nb_consumers = [len(data.consumerGroup.assignment) for data in data_list]
        avg_lag = []
        for data in data_list:
            avg_lag.append(sum(p.lag for p in data.partitionsMetaData.values()) / len(data.consumerGroup.assignment) if len(data.consumerGroup.assignment) > 0 else 0)

        fig, ax1 = plt.subplots(figsize=(14, 7))
        color_arrival = 'tab:orange'
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Avg Total Lag per Consumer', color=color_arrival)
        ax1.axhline(y=(data.consumerGroup.fup * 200 * 0.5), color='red', linestyle='--', label='Avg Up Allowed Lag')
        ax1.axhline(y=(data.consumerGroup.fdown * 200 * 0.5), color='red', linestyle='--', label='Avg Down Allowed Lag')
        ax1.plot(timestamps, avg_lag, color=color_arrival, marker='x', label='Total Lag')
        ax1.tick_params(axis='y', labelcolor=color_arrival)
        ax1.grid(True)
        ax2 = ax1.twinx()
        color_consumers = 'tab:green'
        ax2.set_ylabel('Number of Consumers', color=color_consumers)
        ax2.step(timestamps, nb_consumers, color=color_consumers, label='Number of Consumers', alpha=.05)
        ax2.fill_between(timestamps, nb_consumers, color=color_consumers, step="pre", alpha=0.05)
        ax2.tick_params(axis='y', labelcolor=color_consumers)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.title(f"Avg Total Lag per Consumer over Time — Consumer Group: {group_name}")
        fig.tight_layout()
        filename = f"avg_total_lag_per_consumer_group_{group_name}.png"
        plt.savefig(filename)
        plt.close()

def plot_group_metrics(grouped_data):
    for group_name, data_list in grouped_data.items():
        # Préparation des données
        timestamps = []
        total_lag = []
        arrival_rates = []
        parent_arrival_rates = []
        consumer_counts = []
        upProcessRates = []
        downProcessRates = []
        upLagCapacities = []
        downLagCapacities = []

        for data in data_list:
            # Lag cumulé (somme des lags de toutes les partitions)
            lag_sum = sum(p.lag for p in data.partitionsMetaData.values())
            # Arrival rate (moyenne des arrivalRate de toutes les partitions)
            arrival_rate_sum = 0.
            for p in data.partitionsMetaData.values() :
                arrival_rate_sum += sum(a for a in p.arrivalRate.values())
            # Nombre de consommateurs (nombre de clés dans consumersMetaData)
            consumer_count = len(data.consumersMetaData)

            timestamps.append(data.timestamp)
            total_lag.append(lag_sum)
            arrival_rates.append(arrival_rate_sum)
            parent_arrival_rates.append(data.parentArrivalRate)
            consumer_counts.append(consumer_count)
            upProcessRates.append(data.consumerGroup.upProcessRate)
            downProcessRates.append(data.consumerGroup.downProcessRate)
            upLagCapacities.append(data.consumerGroup.upLagCapacity)
            downLagCapacities.append(data.consumerGroup.downLagCapacity)

        # Création du graphique
        fig, ax1 = plt.subplots(figsize=(14, 7))

        # Axe 1 : Lag cumulé
        color_lag = 'tab:blue'
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Total Lag', color=color_lag)
        ax1.plot(timestamps, total_lag, color=color_lag, marker='o', label='Total Lag')
        ax1.tick_params(axis='y', labelcolor=color_lag)
        ax1.grid(True)

        # Axe 2 : Arrival Rate
        ax2 = ax1.twinx()
        color_arrival = 'tab:orange'
        ax2.set_ylabel('Arrival Rate (sum)', color=color_arrival)
        ax2.plot(timestamps, arrival_rates, color=color_arrival, marker='x', label='Arrival Rate')
        ax2.fill_between(timestamps, upProcessRates, downProcessRates, color=color_arrival, alpha=0.1)
        ax2.tick_params(axis='y', labelcolor=color_arrival)

        # Axe 3 : Nombre de consommateurs
        ax3 = ax1.twinx()
        color_consumers = 'tab:green'
        ax3.spines['right'].set_position(('outward', 120))
        ax3.set_ylabel('Consumer Count', color=color_consumers)
        ax3.set_ylim(-.5, max(consumer_counts) + 0.5)
        ax3.step(timestamps, consumer_counts, color=color_consumers, label='Consumer Count', alpha=.05)
        ax3.fill_between(timestamps, consumer_counts, color=color_consumers, step="pre", alpha=0.05)
        ax3.tick_params(axis='y', labelcolor=color_consumers)

        # Légende combinée
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')

        # Formatage de l'axe X (dates)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.title(f"Metrics over Time — Consumer Group: {group_name}")
        fig.tight_layout()

        # Sauvegarde du graphique
        filename = f"metrics_consumer_group_{group_name}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

def plot_decision_timeline(prometheus_except):
    timestamps = [entry["timestamp"] for entry in prometheus_except]
    exceptions = [entry["exception"] for entry in prometheus_except]
    plt.figure(figsize=(14, 5))
    plt.yticks([0, 1], ['No Exception', 'Exception'])
    plt.fill_between(timestamps, exceptions, color='red', step="pre", alpha=0.1)
    plt.xlabel('Time')
    plt.title('Timeline of MetricResultEmptyException Occurrences')
    plt.grid(True)
    plt.savefig("metric_result_empty_exception_timeline.png")
    
    plt.close()

    print(f"➡️ Graphique généré : metric_result_empty_exception_timeline.png")

# ============================================
# CONSUMER PLOTTING FUNCTIONS
# ============================================

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

def prefab_nb_consumers_over_time(min_time, max_time):
    """
    Produit un graphe unique :
    - courbe en escalier du nombre de consommateurs actifs (axe secondaire, échelle adaptée) pour chaque groupe
    """
    
    results = {}

    plt.figure(figsize=(14, 7))

    for group, uids in consumer_latency_events.items():
        all_change_times = []
        for uid, events in uids.items():
            if events:
                start = min(e.insertion_date for e in events)
                end = max(e.insertion_date for e in events)
                all_change_times.append((start, 'start', uid))
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

        step_times = [p[0] for p in change_points]
        step_counts = [p[1] for p in change_points]

        plt.step(
            step_times,
            step_counts,
            where='post',
            label=f'Group {group}',
            linewidth=2
        )
        
        results[group] = (step_times, step_counts)

    plt.xlabel("Time")
    plt.ylabel("Number of consumers")
    plt.title("Number of active consumers over time per group")
    plt.grid(True)
    plt.legend()
    plt.xlim(min_time, max_time)
    plt.gcf().autofmt_xdate()

    plt.savefig("nb_consumers_over_time.png")
    plt.close()

    print("➡️ Graphique généré : nb_consumers_over_time.png")
    return results

def plot_processing_rate_by_group(grouped_data):
    for group_name, data_list in grouped_data.items():
        timestamps = [data.timestamp for data in data_list]
        fallback_processing_rates = [data.consumerGroup.processingRateFallBack for data in data_list]

        plt.figure(figsize=(14, 7))
        plt.plot(timestamps, fallback_processing_rates, label='Up Process Rate', color='green')
        plt.xlabel('Time')
        plt.ylabel('Processing Rate (events/s)')
        plt.title(f"Processing Rates over Time — Consumer Group: {group_name}")
        plt.grid(True)
        plt.legend()
        plt.xlim(min(timestamps), max(timestamps))
        plt.gcf().autofmt_xdate()
        filename = f"processing_rate_group_{group_name}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

def plot_latency_by_group(waiting_scale, di, min_time, max_time, grouped_data, latency_threshold=500, nb_consumers_per_group=None, total_time_exp=0):
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

        fig, ax1 = plt.subplots(figsize=(16, 6))

        
        replicas_per_minute = defaultdict(set)
        for ev in all_events:
            minute_key = ev.insertion_date.replace(second=0, microsecond=0)
            replicas_per_minute[minute_key].add(ev.consumer_id)
        total_replicas_minute = sum(len(replicas) for replicas in replicas_per_minute.values()) / len(replicas_per_minute) * (total_time_exp / 60) if replicas_per_minute else 0

        color_latency = '#5C669F'
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Latency (ms)", color=color_latency)
        ax1.plot(dates, latencies, marker=".", linestyle="-", color=color_latency, label='Latency')
        ax1.axhline(y=latency_threshold, color='red', linestyle='--')
        ax1.tick_params(axis='y', labelcolor=color_latency)
        ax1.grid(True)
        ax1.set_xlim(min_time, max_time)
        fig.autofmt_xdate()

        ax2 = ax1.twinx()
        if(nb_consumers_per_group and group in nb_consumers_per_group):
            nb_cons_timestamps = [data["timestamp"] for data in nb_consumers_per_group[group]]
            nb_cons_size = [data["size"] for data in nb_consumers_per_group[group]]
            color_consumers = 'tab:green'
            ax2.set_ylabel("Number of consumers", color=color_consumers)
            ax2.step(nb_cons_timestamps, nb_cons_size, where='post', color=color_consumers, alpha=0.7, label='Active consumers', linewidth=2)
            ax2.tick_params(axis='y', labelcolor=color_consumers)

            min_consumers = - 0.5
            max_consumers = max(nb_cons_size) + 0.5
            ax2.set_ylim(min_consumers, max_consumers)
            ax2.set_xlim(min_time, max_time)

        text_str = f"Events > {latency_threshold}ms: {count_high} ({percent_high:.1f}%)"
        ax1.text(0.98, 0.98, text_str, transform=ax1.transAxes,
                 verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        text_str_replicas = f"total RM: {total_replicas_minute:.1f}"
        ax1.text(0.75, 0.98, text_str_replicas, transform=ax1.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontsize=13)
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title(f"Latency and Consumer Count over time — Group: {group}")
        fig.tight_layout()

        filename = f"latency_and_consumers_group_{group}.png"
        plt.savefig(filename, transparent=True)

        ax3 = ax1.twinx()
        timestamps = np.array([e["timestamp"] for e in waiting_scale])
        values = np.array([e["waiting"] for e in waiting_scale])
        ax3.fill_between(timestamps, values, color="red", step="post", alpha=0.1)
        ax3.axes.get_yaxis().set_visible(False)
        ax3.set_xlim(min_time, max_time)

        ax4 = ax1.twinx()
        timestamps = np.array([e["timestamp"] for e in di])
        values = np.array([e["sleep"] for e in di])
        ax4.fill_between(timestamps, values, color="orange", step="post", alpha=0.1)
        ax4.axes.get_yaxis().set_visible(False)
        ax4.set_xlim(min_time, max_time)


        # Légende combinée
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title(f"Latency and Consumer Count over time — Group: {group}")
        fig.tight_layout()

        filename = f"latency_and_consumers_group_{group}_sleep_wait_time.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

def plot_events_by_wsla(min_time, max_time, wsla_threshold=500, nb_consumers_per_group=None):
    """
    Produit un graphe par groupe :
    - Histogramme du nombre d'événements par tranche de latence (WSLA_LOCAL)
    - Lignes de seuil : rouge (200), orange (180), bleu (80)
    - Courbe du nombre de consommateurs actifs (axe secondaire)
    """
    for group, uids in consumer_latency_events.items():
        all_events = []
        for uid, events in uids.items():
            all_events.extend(events)
        all_events = sorted(all_events, key=lambda ev: ev.insertion_date)

        current_time = min_time
        step = timedelta(seconds=(wsla_threshold / 1000))

        step_times = []
        step_counts = []

        while current_time < max_time:
            next_time = current_time + step
            count = sum(1 for ev in all_events if current_time <= ev.insertion_date < next_time)
            step_times.append(current_time)
            step_counts.append(count)
            current_time = next_time

        fig, ax1 = plt.subplots(figsize=(16, 6))
        ax1.plot(step_times, step_counts, color='lightblue', alpha=0.7, label='Event count')
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Number of Events")
        ax1.grid(True)
        ax1.set_xlim(min_time, max_time)
        fig.autofmt_xdate()

        fig.tight_layout()
        filename = f"events_by_wsla_group_{group}.png"
        plt.savefig(filename)
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

def plot_nbconsumer(grouped_data, nb_consumers_per_group, nb_cons_controller_decision_taked):
    """
    Crée un graphe par groupe de consommateurs, affichant :
    - Le nombre de consommateurs actifs (fichier des consommateurs)
    - Le nombre de consommateurs rapporté par le controller
    - Le nombre de consommateurs choisis par le controller
    """

    for group_name, data_list in grouped_data.items():
        controller_timestamps = [data["timestamp"] for data in data_list]
        controller_consumer_counts = [data["consumer"] for data in data_list]

        consumer_timestamps = []
        consumer_counts = []
        if group_name in nb_consumers_per_group:
            consumer_timestamps, consumer_counts = nb_consumers_per_group[group_name]

        decision_timestamp = []
        decision_count = []
        if group_name in nb_cons_controller_decision_taked:
            decision_timestamp = [data["timestamp"] for data in nb_cons_controller_decision_taked[group_name]]
            decision_count = [data["size"] for data in nb_cons_controller_decision_taked[group_name]]
            
        fig, ax = plt.subplots(figsize=(16, 6))

        if consumer_timestamps:
            ax.step(consumer_timestamps, consumer_counts, where='post', color='tab:orange', alpha=0.7, label='Nombre de consommateurs (fichier)')
        if controller_timestamps:
            ax.step(controller_timestamps, controller_consumer_counts, where='post', color='tab:blue', alpha=0.7, label='Nombre de consommateurs (controller)')
        if decision_timestamp:
            ax.step(decision_timestamp, decision_count, where='post', color='tab:green', alpha=0.7, label='Nombre de consommateurs choisis (controller)')

        ax.set_ylim(bottom=0)
        ax.legend(loc='upper left')
        plt.title(f"Évolution du nombre de consommateurs — Groupe : {group_name}")
        plt.xlabel("Temps")
        plt.ylabel("Nombre de consommateurs")
        fig.tight_layout()

        filename = f"consumers_comparison_group_{group_name}.png"
        plt.savefig(filename, dpi=200, bbox_inches='tight')
        plt.close()

        print(f"➡️ Graphique généré : {filename}")

# ============================================
# MAIN
# ============================================


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 mntd-analysis.py <consumer_logs.txt> <controller_logs.txt>")
        sys.exit(1)

    cons_file_path = sys.argv[1]
    ctrl_file_path = sys.argv[2]

    # ========== PARSE CONSUMER LOGS ==========
    print(f"📖 Reading consumer logs from {cons_file_path}")
    with open(cons_file_path, "r") as f:
        for line in f:
            parseLine(line)

    # ========== PARSE CONTROLLER LOGS ==========
    print(f"📖 Reading controller logs from {ctrl_file_path}")
    
    prometheus_data_list = []
    prometheus_data_for_nb_consumer = []
    prometheus_except = []
    controller_waiting_scale_time = []
    di_time = []
    nb_cons_controller_decision_taked = {}

    with open(ctrl_file_path, 'r') as file:
        for line in file:
            if "Pulled data from Prometheus" in line:
                log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
                log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
                prometheus_data_list.append(pulled_data_from_prometheus(line))
                prometheus_data_for_nb_consumer.append(pulled_data_from_prometheus_for_nb_consumer(line))
                prometheus_except.append({"timestamp": log_timestamp, "exception": 0})
            elif "MetricResultEmptyException" in line:
                log_timestamp_str = line.split(" - ")[0].split("WARN")[0].strip()
                log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
                prometheus_except.append({"timestamp": log_timestamp, "exception": 1})
            elif "Waiting consumers group" in line:
                log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
                log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
                controller_waiting_scale_time.append({"timestamp": log_timestamp, "waiting": 1})
            elif "Sleeping for" in line:
                log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
                log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
                sleep_time = float(line.split('Sleeping for ')[1].split(" millisecond")[0])
                controller_waiting_scale_time.append({"timestamp": log_timestamp, "waiting": 0})
                di_time.append({"timestamp": log_timestamp, "sleep": 1})
                di_time.append({"timestamp": log_timestamp + timedelta(milliseconds=sleep_time), "sleep": 0})
            elif "INFO  AdminComponent:66 -  - Deployment" in line:
                log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
                log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
                controller_waiting_scale_time.append({"timestamp": log_timestamp, "waiting": 0})
                di_time.append({"timestamp": log_timestamp, "sleep": 0})
            elif "AssignmentComponent" in line:
                log_timestamp_str = line.split("INFO")[0].strip()
                log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
                info_cons_gr = line.split("Decision for ")[1].split(" : ")
                name_gr = info_cons_gr[0]
                size_gr = int(info_cons_gr[1])
                if(name_gr not in nb_cons_controller_decision_taked):
                    nb_cons_controller_decision_taked[name_gr] = []

                nb_cons_controller_decision_taked.get(name_gr).append({"timestamp": log_timestamp, "size": size_gr})

    # ========== GROUP DATA ==========
    grouped_data = defaultdict(list)
    for all_data in prometheus_data_list:
        for data in all_data:
            group_name = data.consumerGroup.groupName
            grouped_data[group_name].append(data)
    for group_name in grouped_data:
        grouped_data[group_name].sort(key=lambda x: x.timestamp)
    
    grouped_data_for_nb_consumer = defaultdict(list)
    for all_data in prometheus_data_for_nb_consumer:
        for data in all_data:
            group_name = data["name"]
            grouped_data_for_nb_consumer[group_name].append(data)
    for group_name in grouped_data_for_nb_consumer:
        grouped_data_for_nb_consumer[group_name].sort(key=lambda x: x["timestamp"])
    

    # ========== PREPARE TIME BOUNDS ==========
    min_time, max_time = get_global_time_bounds()
    sort_all_events_by_timestamp()

    controller_waiting_scale_time.sort(key=lambda x: x["timestamp"])
    di_time.sort(key=lambda x: x["timestamp"])
    for group in nb_cons_controller_decision_taked:
        nb_cons_controller_decision_taked[group].sort(key=lambda x: x["timestamp"])

    # ========== GENERATE PLOTS ==========
    print("\n🎨 Generating plots...")
    
    nb_consumers_per_group = prefab_nb_consumers_over_time(min_time, max_time)
    plot_nbconsumer(grouped_data_for_nb_consumer, nb_consumers_per_group, nb_cons_controller_decision_taked)
    
    duration = (max_time - min_time).total_seconds()
    plot_latency_by_group(controller_waiting_scale_time, di_time, min_time, max_time, grouped_data, nb_consumers_per_group=nb_cons_controller_decision_taked, total_time_exp=duration)
    
    plot_decision_timeline(prometheus_except)
    plot_latency_by_consumer(min_time, max_time)
    plot_events_by_wsla(min_time, max_time, nb_consumers_per_group=nb_cons_controller_decision_taked)
    plot_group_arrival_rate(grouped_data)
    plot_group_lag(grouped_data)
    plot_processing_rate_by_group(grouped_data)
    
    print("\n✅ All plots generated successfully!")
    print(f"⏱️ Total analysis duration: {duration:.2f} seconds")
