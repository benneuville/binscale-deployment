import sys
import datetime
import matplotlib.pyplot as plt
from typing import List, Dict
import re
from datetime import datetime

consumers_decisions_by_time = []
collections_by_time = []

class ConsumerGroup:
    def __init__(self, consumers):
        self.consumers = consumers
        
class Consumer:
    def __init__(self, name):
        self.name = name
        self.records = []

class Decission:
    def __init__(self, insertion_date, consumerGroup, decission):
        self.insertion_date = insertion_date
        self.consumerGroup = consumerGroup
        self.decission = decission


def get_global_time_bounds():
    all_dates = []

    for group in consumer_latency_events.values():
        for uid, events in group.items():
            for ev in events:
                all_dates.append(ev.insertion_date)

    if not all_dates:
        return None, None

    return min(all_dates), max(all_dates)


def uncollected_exception(line):
    #TODO, parse the line to extract relevant info
    pass

class PartitionMetaData:
    def __init__(self, partition, lag, arrival_rate, latency, processing_time, processing_count):
        self.partition = partition
        self.lag = lag
        self.arrival_rate = arrival_rate
        self.latency = latency
        self.processing_time = processing_time
        self.processing_count = processing_count

class ConsumerMetaData:
    def __init__(self, consumer_id, avg_processing_capacity):
        self.consumer_id = consumer_id
        self.avg_processing_capacity = avg_processing_capacity

class ConsumerGroupMetaData:
    def __init__(self, consumer_group, partitions_meta_data, consumers_meta_data, parent_arrival_rate, collection_timestamp):
        self.consumer_group = consumer_group
        self.partitions_meta_data = partitions_meta_data  # {partition_id: PartitionMetaData}
        self.consumers_meta_data = consumers_meta_data    # {consumer_id: ConsumerMetaData}
        self.parent_arrival_rate = parent_arrival_rate
        self.collection_timestamp = collection_timestamp

def pulled_data_from_prometheus(line):
    # Extraction de l'horodatage de collecte
    timestamp_str = line.split("INFO")[0].strip()
    collection_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

    # Extraction de la liste des ConsumerGroupMetaData
    groups_data_str = line.split("Pulled data from Prometheus : [")[1].rstrip("]")
    groups = []
    for group_str in groups_data_str.split("ConsumerGroupMetaData{"):
        if not group_str.strip():
            continue
        group_str = "ConsumerGroupMetaData{" + group_str
        group = parse_consumer_group(group_str, collection_timestamp)
        groups.append(group)

    return groups

def parse_consumer_group(group_str, collection_timestamp):
    # Extraction du nom du groupe
    consumer_group = group_str.split("consumerGroup=")[1].split(",")[0]

    # Extraction des métadonnées des partitions
    partitions_str = group_str.split("partitionsMetaData={")[1].split("}, consumersMetaData=")[0]
    partitions_meta_data = {}
    for partition_str in partitions_str.split("Partition{id="):
        if not partition_str.strip() or "PartitionMetaData" not in partition_str:
            continue
        partition = parse_partition(partition_str)
        partitions_meta_data[partition["id"]] = PartitionMetaData(**partition)

    # Extraction des métadonnées des consommateurs
    consumers_str = group_str.split("consumersMetaData={")[1].split("}, parentArrivalRate=")[0]
    consumers_meta_data = {}
    for consumer_str in consumers_str.split("Consumer{id="):
        if not consumer_str.strip() or "ConsumerMetaData" not in consumer_str:
            continue
        consumer = parse_consumer(consumer_str)
        consumers_meta_data[consumer["id"]] = ConsumerMetaData(**consumer)

    # Extraction du parentArrivalRate
    parent_arrival_rate = float(group_str.split("parentArrivalRate=")[1].split("}")[0])

    return ConsumerGroupMetaData(
        consumer_group=consumer_group,
        partitions_meta_data=partitions_meta_data,
        consumers_meta_data=consumers_meta_data,
        parent_arrival_rate=parent_arrival_rate,
        collection_timestamp=collection_timestamp,
    )

def parse_partition(partition_str):
    partition_id = int(partition_str.split("id=")[1].split("}=")[0])
    partition_data = partition_str.split("PartitionMetaData{")[1].split("}")[0]
    partition_meta = {}
    for field in partition_data.split(","):
        if "=" in field:
            key, value = field.split("=")
            partition_meta[key.strip()] = float(value) if "." in value else int(value)
    partition_meta["partition"] = partition_id
    return partition_meta

def parse_consumer(consumer_str):
    consumer_id = int(consumer_str.split("id=")[1].split("}=")[0])
    consumer_data = consumer_str.split("ConsumerMetaData{")[1].split("}")[0]
    consumer_meta = {}
    for field in consumer_data.split(","):
        if "=" in field:
            key, value = field.split("=")
            consumer_meta[key.strip()] = float(value) if "." in value else int(value)
    consumer_meta["consumer_id"] = consumer_id
    return consumer_meta


def parseLine(line):
    global consumer_latency_events
    if "MetricResultEmptyException" in line:
        uncollected_exception(line)
    if "Pulled data from Prometheus" in line:
        print("➡️ Parsing Prometheus data...")
        print(pulled_data_from_prometheus(line))




# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mtnd-analyse.py <file_log.txt>")
        sys.exit(1)

    file_path = sys.argv[1]


    with open(file_path, "r") as f:
        for line in f:
            parseLine(line)
    
    min_time, max_time = get_global_time_bounds()
    
if __name__ == "__main__":
    main()
