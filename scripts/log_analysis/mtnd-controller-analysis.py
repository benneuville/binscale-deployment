import sys
import datetime
import matplotlib.pyplot as plt

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
    print(line)

def parseLine(line):
    global consumer_latency_events
    if "MetricResultEmptyException" in line:
        uncollected_exception(line)




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
    