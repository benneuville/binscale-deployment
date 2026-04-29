import sys
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Dict
import re
from datetime import datetime, timedelta
import json
from collections import defaultdict

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
    def __init__(self, wsla, inputTopic, consumerName, kafkaGroupName, maxDefinedProcessingRate, topicPartitions, lastUpScaleDecision, assignment, fup, fdown, name, groupName, upProcessRate, downProcessRate, upLagCapacity, downLagCapacity):
        self.wsla = wsla
        self.inputTopic = inputTopic
        self.consumerName = consumerName
        self.kafkaGroupName = kafkaGroupName
        self.maxDefinedProcessingRate = maxDefinedProcessingRate
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
            maxDefinedProcessingRate=data["consumerGroup"]["maxDefinedProcessingRate"],
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
        # ax1.fill_between(timestamps, upLagCapacities, downLagCapacities, color=color_lag, alpha=0.1)
        ax1.tick_params(axis='y', labelcolor=color_lag)
        ax1.grid(True)

        # Axe 2 : Arrival Rate
        ax2 = ax1.twinx()
        color_arrival = 'tab:orange'
        ax2.set_ylabel('Arrival Rate (sum)', color=color_arrival)
        ax2.plot(timestamps, arrival_rates, color=color_arrival, marker='x', label='Arrival Rate')
        ax2.fill_between(timestamps, upProcessRates, downProcessRates, color=color_arrival, alpha=0.1)
        ax2.tick_params(axis='y', labelcolor=color_arrival)

        # Axe 4 : ParentArrivalRate
        ax4 = ax1.twinx()
        # color_pArrivalRate = 'tab:red'
        # ax4.spines['right'].set_position(('outward', 60))
        # ax4.set_ylabel('Parent Arrival Rate (sum)', color = color_pArrivalRate)
        # ax4.plot(timestamps, parent_arrival_rates, color_pArrivalRate, marker='x', label='Parent Arrival Rate')
        # ax4.tick_params(axis='y', labelcolor=color_pArrivalRate)

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
        lines4, labels4 = ax4.get_legend_handles_labels()
        ax1.legend(lines1 + lines2 + lines3 + lines4, labels1 + labels2 + labels3 + labels4, loc='upper left')

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
    # plt.step(timestamps, exceptions, color='red', alpha=0.1)
    plt.yticks([0, 1], ['No Exception', 'Exception'])
    plt.fill_between(timestamps, exceptions, color='red', step="pre", alpha=0.1)
    plt.xlabel('Time')
    plt.title('Timeline of MetricResultEmptyException Occurrences')
    plt.grid(True)
    plt.savefig("metric_result_empty_exception_timeline.png")
    
    plt.close()

    print(f"➡️ Graphique généré : metric_result_empty_exception_timeline.png")

if __name__ == "__main__":
    log_file_path = sys.argv[1]

    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    prometheus_data_list = []
    prometheus_except = []
    controller_waiting_scale_time = []
    di_time = []
    for line in lines:
        if "Pulled data from Prometheus" in line:
            log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
            log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')
            prometheus_data_list.append(pulled_data_from_prometheus(line))
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

    
        
    grouped_data = defaultdict(list)
    for all_data in prometheus_data_list:
        for data in all_data:
            group_name = data.consumerGroup.kafkaGroupName
            grouped_data[group_name].append(data)
    
    for group_name in grouped_data:
        grouped_data[group_name].sort(key=lambda x: x.timestamp)
        
    prometheus_except.sort(key=lambda x: x["timestamp"])

    plot_group_metrics(grouped_data)

    plot_decision_timeline(prometheus_except)

    plot_group_arrival_rate(grouped_data)

    plot_group_lag(grouped_data)