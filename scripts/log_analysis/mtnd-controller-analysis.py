import sys
import datetime
import matplotlib.pyplot as plt

 = []

class ConsumerGroup:
    def __init__(self, consumers):
        self.consumers = consumers
        

class Consumer:
    def __init__(self, name):
        self.name = name
        self.records = []


class Decission:
    def __init__(self, consumerGroup, decission):
        self.consumerGroup = consumerGroup
        self.decission = decission



def parseLine(line):
    global consumer_latency_events
    if "MetricResultEmptyException" in line:
        print(line)