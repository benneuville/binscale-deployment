import sys
import datetime
import matplotlib.pyplot as plt
import numpy as np

# date_list = []
# lag_list = []

lag_controler_events = []

insertion_date = []
processing_date = []

# insertion_date_for_latency =[]
# latency_list = []

#a dictionnary, key is consumer uid, value is a tuple (date, latency)
consumer_latency_events ={}

# lag_list_from_events = []
# date_list_from_events = []
lag_events = []

#a dictionnary, key is consumer uid, value is a list of dates
consumer_commit_events = {}

def parseInsertionDate(line):
    try:
        date_str = line.split("insertion time is ")[1].split(",")[0]
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        insertion_date.append(parsed_date)
        # print("Insertion date: ", parsed_date)
    except Exception as e:
        print(f"Error parsing insertion date: {e}, line: {line}")

def parseProcessingDate(line):
    try:
        date_str = line.split("processing time is ")[1].split("\"")[0]
        date_str=date_str.replace("\n", "")
        # print(date_str)
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        processing_date.append(parsed_date)
        # print("Processing date: ", parsed_date  )
    except Exception as e:
        print(f"Error parsing processing date: {e}, line: {line}")

def parseTotalLag(line):
    # print("parseTotalLag", line)
    global lag_list
    try:
        date_str = line.split("at ")[1].strip()
        # print(date_str)
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        lag = int(line.split("total lag ")[1].split(",")[0].split(" ")[0])
        # print(parsed_date)
        # date_list.append(parsed_date)
        # lag_list.append(lag)
        lag_controler_events.append((parsed_date, lag))
    except Exception as e:
        print(f"Error parsing total lag: {e}, line: {line}")

def parseLatency(line):
    # global insertion_date_for_latency
    # global latency_list
    global consumer_latency_events
    try:
        uid = line.split(" ")[0]
        date_str = line.split("insertion time is ")[1].split(",")[0]
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        latency = int(line.split("latency is ")[1].split(",")[0])
        # insertion_date_for_latency.append(parsed_date)
        # latency_list.append(latency)
        if uid in consumer_latency_events:
            consumer_latency_events[uid].append((parsed_date, latency))
        else :
            consumer_latency_events[uid] = [(parsed_date, latency)]
        # latency_events.append((parsed_date, latency))
    except Exception as e:
        print(f"Error parsing latency: {e}, line: {line}")

def parseConsumerOffsetTime(line):
    try:
        uid = line.split(" ")[0]
        # print("Consumer uid: ", uid)
        date_str = line.split("Committed offset at time ")[1].replace("\n", "")
        #print('--',date_str)
        parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%YT%H:%M:%S.%f')
        if uid in consumer_commit_events:
            consumer_commit_events[uid].append(parsed_date)
        else:
            consumer_commit_events[uid] = [parsed_date]
        # print(parsed_date)
    except Exception as e:
        print(f"Error parsing consumer offset time: {e}, line: {line}")

def parseLine(line):
    if "total lag" in line:
        parseTotalLag(line)
    
    if "insertion time is" in line:
        parseInsertionDate(line)
        parseLatency(line)
    if "processing time is" in line:
        parseProcessingDate(line)
    
    if "Committed offset" in line:
        parseConsumerOffsetTime(line)
        

def compute_lag_from_events(decision_interval):
    global insertion_date
    global processing_date
    # global lag_list_from_events
    # global date_list_from_events
    print('Computing lag from events')
    # insertion_date.sort()
    # processing_date.sort()
    first_date = insertion_date[0]
    last_date = insertion_date[-1]
    print(len(insertion_date), len(processing_date))
    next_date = first_date + datetime.timedelta(milliseconds=decision_interval)
    event_in = 0
    event_out = 0
    while next_date < last_date:
        while event_in < len(insertion_date) and insertion_date[event_in] <= next_date:
            event_in += 1
        while event_out < len(processing_date) and processing_date[event_out] <= next_date:
            event_out += 1
        lag = event_in - event_out
        # print("Next date: ", next_date, "Lag: ", lag, "Event in: ", event_in, "Event out: ", event_out)
        lag_events.append((next_date, lag))
        # lag_list_from_events.append(lag)
        # date_list_from_events.append(next_date)
        next_date = next_date + datetime.timedelta(milliseconds=decision_interval)
    return [(processing_date[i] - insertion_date[i])for i in range(min(len(insertion_date), len(processing_date)))]

def compute_decision_interval():
    # intervals = [(date_list[i + 1] - date_list[i]).total_seconds() * 1000 for i in range(len(date_list) - 1)]
    # for i in range(len(lag_controler_events) - 1):
    #     if (lag_controler_events[i + 1][0] - lag_controler_events[i][0]).total_seconds() * 1000 <0 :
    #         print("xxxx", lag_controler_events[i + 1][0], lag_controler_events[i][0], (lag_controler_events[i + 1][0] - lag_controler_events[i][0]).total_seconds() * 1000)
    intervals = [(lag_controler_events[i + 1][0] - lag_controler_events[i][0]).total_seconds() * 1000 for i in range(len(lag_controler_events) - 1)]
    # print(lag_controler_events[ 1][0],lag_controler_events[0][0], (lag_controler_events[ 1][0]-lag_controler_events[0][0]).total_seconds()*1000)
    # print("Intervals: ", intervals)
    # print(np.average(intervals))
    # exit(1)
    return abs(int(np.average(intervals)))

def plot_lag(sourceFileName, decision_interval, decision_interval_from_events):
    # global date_list
    # global lag_list
    print("Source file name: ", sourceFileName)
    sourceFileName = sourceFileName.split("/")[-1]
    sourceFileName = sourceFileName.split(".")[0]
    plt.figure(figsize=(10, 5))
    plt.title("Lag with decision interval " + str(decision_interval) + "ms")
    plt.xlabel('Time')
    # print("first date ", date_list[0], "last date ", date_list[-1])
    # date_list = [date - date_list[0] for date in date_list]
    # date_list = [date.total_seconds() * 1000 for date in date_list]
    # date_list_from_events = [x * int(decision_interval_from_events) for x in range(len(lag_list_from_events))]
    #there is an issue, we need to truncate the lag_list to the same length as lag_list_from_events
    # lag_list = lag_list[:len(lag_events)]
    # date_list = date_list[:len(lag_events)]
    
    

    # processing_date.sort()
    # insertion_date.sort()
    # date_list.sort()
    # print(insertion_date[0], processing_date[0])
    # plt.plot(insertion_date[:100], [1]*len(insertion_date[:100]),label="Insertion date")
    # plt.plot(processing_date[:100], [1.2]*len(processing_date[:100]),label="Processing date")
    plt.plot(*zip(*lag_controler_events), label="Lag from commit")
    plt.plot(*zip(*lag_events), label="Lag from events (decision interval " + str(decision_interval_from_events) + "ms)")
   
    #rotate x axis labels
    plt.xticks(rotation=30)
    #only hour and seconds
    plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.MinuteLocator())
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))
   
    # print(date_list[0], date_list_from_events[0])
    plt.legend()
    plt.ylabel('Lag')
    plt.savefig("lag-" + sourceFileName + "-" + str(decision_interval) + "ms.png")
    print("output file: ", "lag-" + sourceFileName + "-" + str(decision_interval) + "ms.png")
    # print(len(date_list), len(lag_list))
    # print(date_list[-10], date_list_from_events[-10])
    # print(lag_list_from_events[10:100])

def plot_global_consumer_latency_list():
    # merge all latency events
    latency_events = []
    for key in consumer_latency_events:
        latency_events += consumer_latency_events[key]
    latency_events.sort(key=lambda x: x[0])
    
    plt.figure(figsize=(10, 5))
    plt.title("Latency")
    plt.xlabel('Time')
    plt.plot(*zip(*latency_events), label="Latency")
    plt.legend()
    plt.ylabel('Latency')
    plt.savefig("latency.png")

#region plot consumer latency
def plot_consumer_latency():
    num_of_groups = len(consumer_latency_events.keys())
    fig, axs = plt.subplots(num_of_groups, 1, figsize=(30, 20), facecolor='w', edgecolor='k', sharex='all')
    fig.subplots_adjust(hspace=.5, wspace=.001)
    axs = axs if isinstance(axs, np.ndarray) else [axs]
    i=0
    for uid in consumer_latency_events.keys():
        axs[i].title.set_text("")
        events = consumer_latency_events[uid]
        events.sort(key=lambda x: x[0])
        axs[i].plot(*zip(*events), label=str(uid))
        axs[i].set_ylabel("Consumer " + str(i))
        i+=1
        
        #rotate x axis labels
    plt.xticks(rotation=30)
    #only hour and seconds
    plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.MinuteLocator())
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))
    plt.savefig('latency_per_pod.png')
    plt.close()        

    # for key in consumer_latency_events:
    #     dates = consumer_latency_events[key]
    #     dates.sort()
    #     latencies = [val[1] for val in dates]
    #     x = [i for i in range(0, len(latencies))]
    #     plt.figure(figsize=(30, 5))
    #     plt.title("Latency for consumer " + key)
    #     plt.xlabel('Time')
    #     plt.plot(x, latencies, label="Latency")
    #     plt.legend()
    #     plt.ylabel('Latency')
    #     plt.savefig("latency-" + key + ".png")
    #     print("output file: ", "latency-" + key + ".png")
    

def plot_received_events(interval):
    global insertion_date
    received_events_per_interval = []
    first_date = insertion_date[0]
    next_date = first_date + datetime.timedelta(milliseconds=interval)
    event_in = 0
    # event_out = 0
    # while next_date < last_date:
    for i in range(len(insertion_date)):
        if insertion_date[i] <= next_date:
            event_in += 1
        else:
            # if next_date - first_date < datetime.timedelta(minutes=1):

            received_events_per_interval.append((next_date, event_in))
            next_date = next_date + datetime.timedelta(milliseconds=interval)
            event_in = 0
            # print(event_in)
        # while event_in < len(insertion_date) and insertion_date[event_in] <= next_date:
        #     event_in += 1
    plt.figure(figsize=(30, 5))
    plt.title("Received events per " + str(interval)+ "ms")
    plt.xlabel('Time')
    
    #plt.plot(*zip(*received_events_per_interval), label="Events")
    # x = [val[0] for val in received_events_per_interval]
    # y = [val[1] for val in received_events_per_interval]
    # print(y)
    x,y = [*zip(*received_events_per_interval)]
    # print(x)
    # print(y)
    plt.bar(x,y, label="Events", align='center', width=0.9*np.min(np.diff(x)))
    plt.legend()
    plt.ylabel('#events')
    plt.savefig("events_in.png")
    print("output file: ", "events_in.png")

def plot_processed_events(interval):
    global processing_date
    processed_events_per_interval = []
    first_date = processing_date[0]
    next_date = first_date + datetime.timedelta(milliseconds=interval)
    event_in = 0
    # event_out = 0
    # while next_date < last_date:
    for i in range(len(insertion_date)):
        if processing_date[i] <= next_date:
            event_in += 1
        else:
            #append only if next_date is between two dates
            # if next_date - first_date < datetime.timedelta(minutes=1):
            processed_events_per_interval.append((next_date, event_in))
            next_date = next_date + datetime.timedelta(milliseconds=interval)
            event_in = 0
            # print(event_in)
        # while event_in < len(insertion_date) and insertion_date[event_in] <= next_date:
        #     event_in += 1
    plt.figure(figsize=(30, 5))
    plt.title("Processed events per " + str(interval)+ "ms")
    plt.xlabel('Time')
    x,y = [*zip(*processed_events_per_interval)]
    # plt.plot(*zip(*processed_events_per_interval), label="Events")
    plt.bar(x,y, label="Events", align='center', width=0.9*np.min(np.diff(x)))

    plt.legend()
    plt.ylabel('#events')
    plt.savefig("events_out.png")
    print("output file: ", "events_out.png")
    # plt.show()


def plot_duration_between_commits() :
    for key in consumer_commit_events:
        # print("Consumer: ", key)
        dates = consumer_commit_events[key]
        dates.sort()
        durations = [(dates[i] - dates[i-1]).total_seconds()*1000 for i in range(1, len(dates))]
        # print(durations)
       
        x = [i for i in range(0, len(durations))]
        if (len(x) > 1):
        # print(x)
            plt.figure(figsize=(30, 5))
            plt.title("Duration between commits for consumer " + key)
            plt.xlabel('Time')
            plt.bar(x,durations,  label="Duration between commits",width=0.9*np.min(np.diff(x)))
            plt.legend()
            plt.ylabel('Duration')
            plt.savefig("duration-" + key + ".png")
            print("output file: ", "duration-" + key + ".png")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lagAnalyzer.py <path_to_log> <path_to_log2> [decision_interval]")
        sys.exit(1)
    print(sys.argv)

    for i in sys.argv[1:3]:
        print("Processing file: ", i)
        try:
            with open(i, "r") as file:
                for line in file:
                    if len(line.strip()) > 0:  # Skip empty lines
                        parseLine(line)
        except Exception as e:
            print(f"Error processing file {i}: {e}")

    #sort events by date
    lag_controler_events.sort(key=lambda x: x[0])
    processing_date.sort()
    insertion_date.sort()
    # consumer_latency_events.sort(key=lambda x: x[0])


    decision_interval = 100#compute_decision_interval()
    print("Decision interval: ", decision_interval)
    if len(sys.argv) == 4:
        decision_interval_from_events = int(sys.argv[3])
    else:
        decision_interval_from_events = decision_interval
    print("Decision interval from events: ", decision_interval_from_events)
    compute_lag_from_events(decision_interval_from_events)
 

    plot_lag(sys.argv[1], decision_interval, decision_interval_from_events)
    plot_global_consumer_latency_list()
    plot_received_events(500)
    plot_processed_events(500)
    plot_duration_between_commits()
    plot_consumer_latency()