from jinja2 import Template
import yaml
import sys

WORLOAD = "workload"
LATENCY = "latency"
CONTROLLER = "controller"
KAFKA_TOPIC = "kafka-topic"
MONITORING_CONSUMER = "monitoring-consumer"


if len(sys.argv) < 2:
    print("Usage: python generate_deployment.py <file.yaml> <image-tag>")
    sys.exit(1)

file_path = sys.argv[1]
image_tag = sys.argv[2]

def is_workload_node(type):
    return type == WORLOAD

def edge_check(edge, graph):
    if graph[edge["to"]] is None:
        raise ValueError(f"Node {edge['to']} not found in graph")
    if graph[edge["from"]] is None:
        raise ValueError(f"Node {edge['from']} not found in graph")
    if graph[edge["to"]]["type"] == WORLOAD:
        raise ValueError("Workload nodes cannot be destination nodes")

templates = {}
### Load templates

with open("experience/templates/latency.yaml.j2") as f:
    templates[LATENCY] = Template(f.read())

with open("experience/templates/producer.yaml.j2") as f:
    templates[WORLOAD] = Template(f.read())

with open("experience/templates/controller.yaml.j2") as f:
    templates[CONTROLLER] = Template(f.read())

with open("experience/templates/kafka-topic.yaml.j2") as f:
    templates[KAFKA_TOPIC] = Template(f.read())

with open("experience/templates/monitoring-consumer.yaml.j2") as f:
    templates[MONITORING_CONSUMER] = Template(f.read())

with open("experience/templates/controller.yaml.j2") as f:
    templates[CONTROLLER] = Template(f.read())

## Load graph
with open(file_path) as f:
    graph = yaml.safe_load(f)

### Generate deployment files
edges = {}
nodes = {}

controller = graph["controller"]

controller["params"]["decision_interval"] = controller["params"]["metrics"]["request_time_range"] * 1000

for node in graph["nodes"]:
    node["targets"] = []
    nodes[node["id"]] = node

for edge in graph["edges"]:
    tmp_edge = {
        "from": edge["from"],
        "to": edge["to"],
        "from_group_id": nodes[edge["from"]]["params"]["group_id"] if is_workload_node(nodes[edge["from"]]["type"]) == False else None,
        "to_group_id": nodes[edge["to"]]["params"]["group_id"],
        "weight": edge.get("weight", 1),
        "partitions": nodes[edge["to"]].get("partitions", 10),
        "topic_name": f"topic-{edge['to']}",
        "to_wsla": nodes[edge["to"]]["params"].get("wsla", None)
    }
    edge_check(tmp_edge, nodes)
    
    nodes[tmp_edge["to"]]["params"]["topic_name"] = tmp_edge["topic_name"]

    if is_workload_node(nodes[tmp_edge["from"]]["type"]):
        nodes[tmp_edge["from"]]["params"]["partition_weights"] = ','.join(["1"] * tmp_edge["partitions"])
        nodes[tmp_edge["from"]]["params"]["topic_name"] = tmp_edge["topic_name"]
    else:
        nodes[tmp_edge["from"]]["targets"].append({ "topic_name": tmp_edge["topic_name"], "ratio": tmp_edge["weight"] })

    edges[tmp_edge["topic_name"]] = tmp_edge

print("🚂 Generating Kafka topics...")
edges_topic_gen = []
for edge in edges.values():
    edges_topic_gen.append(templates[KAFKA_TOPIC].render(edge))

# Output all topics in one file in "/generated/kafka-topics.yaml"
with open("experience/generated/kafka-topics.yaml", "w") as f:
    f.write("\n---\n".join(edges_topic_gen))

print("✅ Kafka topics generated")

print("🚂 Generating Service nodes...")
nodes_service_gen = []
for node in [v for v in nodes.values() if v["type"] == LATENCY]:
    nodes_service_gen.append(templates[node["type"]].render(node=node, image_tag=image_tag))
nodes_service_gen.append(templates[MONITORING_CONSUMER].render(nodes=[v for v in nodes.values() if v["type"] == LATENCY])) # Add monitoring consumer for all latency nodes
# Output all service nodes in one file in "/generated/latency.yaml"
with open("experience/generated/latency.yaml", "w") as f:
    f.write("\n---\n".join(nodes_service_gen))

print("✅ Service nodes generated")

print("🚂 Generating Workload nodes...")
nodes_workload_gen = []
for node in [v for v in nodes.values() if v["type"] == WORLOAD]:
    nodes_workload_gen.append(templates[node["type"]].render(node=node, image_tag=image_tag))
# Output all workload nodes in one file in "/generated/workload.yaml"
with open("experience/generated/workload.yaml", "w") as f:
    f.write("\n---\n".join(nodes_workload_gen))

print("✅ Workload nodes generated")

print("🚂 Generating Controller...")

edges_filter = [e for e in edges if(nodes[edges[e]["from"]]["type"]==LATENCY and nodes[edges[e]["to"]]["type"]==LATENCY)]

with open("experience/generated/controller.yaml", "w") as f:
    f.write(templates[CONTROLLER].render(controller=controller,
                                         edges={e: edges[e] for e in edges_filter},
                                         edges_full=edges,
                                         nodes=[v for v in nodes.values() if v["type"] == LATENCY],
                                         image_tag=image_tag))


print("✅ Controller generated")