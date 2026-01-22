import sys
import datetime
import matplotlib.pyplot as plt
from typing import List, Dict
import re
from datetime import datetime
import json

class Partition:
    def __init__(self, id, lag=0, arrivalRate=0.0, processingTime=0.0, processingCount=0.0, latency=0.0, processingCapacity=0.0, lagRebalancing=0.0):
        self.id = id
        self.lag = lag
        self.arrivalRate = arrivalRate
        self.processingTime = processingTime
        self.processingCount = processingCount
        self.latency = latency
        self.processingCapacity = processingCapacity
        self.lagRebalancing = lagRebalancing

class Consumer:
    def __init__(self, id, assignedPartitions, avgProcessingCapacity=0.0):
        self.id = id
        self.assignedPartitions = assignedPartitions
        self.avgProcessingCapacity = avgProcessingCapacity

class ConsumerGroup:
    def __init__(self, wsla, inputTopic, consumerName, kafkaGroupName, maxDefinedProcessingRate, topicPartitions, lastUpScaleDecision, assignment, fup, fdown, name, groupName):
        self.wsla = wsla
        self.inputTopic = inputTopic
        self.consumerName = consumerName
        self.kafkaGroupName = kafkaGroupName
        self.maxDefinedProcessingRate = maxDefinedProcessingRate
        self.topicPartitions = topicPartitions
        self.lastUpScaleDecision = datetime.strptime(lastUpScaleDecision, '%m/%d/%YT%H:%M:%S.%f')
        self.assignment = assignment
        self.fup = fup
        self.fdown = fdown
        self.name = name
        self.groupName = groupName

class PrometheusData:
    def __init__(self, timestamp, consumerGroup, partitionsMetaData, consumersMetaData, parentArrivalRate, avgEventProcessingRate, totalArrivalRate, maxAverageArrivalRate, avgParentArrivalRate, minAverageArrivalRate, maxLagCapacity, minLagCapacity):
        self.timestamp = timestamp
        self.consumerGroup = consumerGroup
        self.partitionsMetaData = partitionsMetaData
        self.consumersMetaData = consumersMetaData
        self.parentArrivalRate = parentArrivalRate
        self.avgEventProcessingRate = avgEventProcessingRate
        self.totalArrivalRate = totalArrivalRate
        self.maxAverageArrivalRate = maxAverageArrivalRate
        self.avgParentArrivalRate = avgParentArrivalRate
        self.minAverageArrivalRate = minAverageArrivalRate
        self.maxLagCapacity = maxLagCapacity
        self.minLagCapacity = minLagCapacity

def pulled_data_from_prometheus(line):
    # Extraction du timestamp de la ligne de log
    log_timestamp_str = line.split(" - ")[0].split("INFO")[0].strip()
    log_timestamp = datetime.strptime(log_timestamp_str, '%Y-%m-%d %H:%M:%S')

    # Extraction de la partie JSON
    json_start = line.find('[')
    json_end = line.rfind(']')
    json_str = line[json_start:json_end+1]
    data_list = json.loads(json_str)

    data = data_list[0]

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
            processingCapacity=partition_data["processingCapacity"],
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
            avgProcessingCapacity=consumer_data["avgProcessingCapacity"]
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
        groupName=data["consumerGroup"]["groupName"]
    )

    # Création de l'objet PrometheusData
    prometheus_data = PrometheusData(
        timestamp=log_timestamp,
        consumerGroup=consumer_group,
        partitionsMetaData=partitions,
        consumersMetaData=consumers,
        parentArrivalRate=data["parentArrivalRate"],
        avgEventProcessingRate=data["avgEventProcessingRate"],
        totalArrivalRate=data["totalArrivalRate"],
        maxAverageArrivalRate=data["maxAverageArrivalRate"],
        avgParentArrivalRate=data["avgParentArrivalRate"],
        minAverageArrivalRate=data["minAverageArrivalRate"],
        maxLagCapacity=data["maxLagCapacity"],
        minLagCapacity=data["minLagCapacity"]
    )

    return prometheus_data

if __name__ == "__main__":
    log_file_path = sys.argv[1]

    with open(log_file_path, 'r') as file:
        lines = file.readlines()

    prometheus_data_list = []
    for line in lines:
        if "Pulled data from Prometheus" in line:
            prometheus_data = pulled_data_from_prometheus(line)
            prometheus_data_list.append(prometheus_data)

    # Example: Print the timestamps of the pulled data
    for data in prometheus_data_list:
        print(f"Data pulled at: {data.timestamp}")

