from jinja2 import Template
import yaml
import sys

WORLOAD = "workload"
LATENCY = "latency"
CONTROLLER = "controller"
KAFKA_TOPIC = "kafka-topic"
MONITORING_CONSUMER = "monitoring-consumer"
PRE_PULL_IMAGE = "pre-pull-image"
E2E_ANALYZER = "e2e-analyzer"


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

with open("experience/templates/pre-pull-image.yaml.j2") as f:
    templates[PRE_PULL_IMAGE] = Template(f.read())

with open("experience/templates/e2e-analyzer.yaml.j2") as f:
    templates[E2E_ANALYZER] = Template(f.read())


## Load graph
with open(file_path) as f:
    graph = yaml.safe_load(f)

### Generate deployment files
edges = {}
nodes = {}

filtered_edges = []

controller = graph["controller"]

if controller["params"].get("decision_interval", None) is None:
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
        
        filtered_edges.append(
            {
                'from': edge["from"],
                "to": edge["to"],
                "weight": edge.get("weight", 1)
            }
        )

    edges[tmp_edge["topic_name"]] = tmp_edge

print("🚂 Generating Kafka topics...")
edges_topic_gen = []
for edge in edges.values():
    edges_topic_gen.append(templates[KAFKA_TOPIC].render(edge))

edges_topic_gen.append(templates[KAFKA_TOPIC].render({"topic_name" : "e2e_state", "partitions": 10}))
edges_topic_gen.append(templates[KAFKA_TOPIC].render({"topic_name" : "final_queue", "partitions": 10}))

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
with open("experience/generated/controller.yaml", "w") as f:
    f.write(templates[CONTROLLER].render(controller=controller,
                                         edges=filtered_edges,
                                         edges_full=edges,
                                         nodes=[v for v in nodes.values() if v["type"] == LATENCY],
                                         image_tag=image_tag))
print("✅ Controller generated")

print("🚂 Generating E2E Analyzer...")
with open("experience/generated/e2e-analyzer.yaml", "w") as f:
    f.write(templates[E2E_ANALYZER].render(nodes=[v for v in nodes.values() if v["type"] == LATENCY], image_tag=image_tag))

print("✅ E2E Analyzer generated")

print("🚂 Generating pre-pull image job...")
with open("experience/generated/pre-pull-image.yaml", "w") as f:
    f.write(templates[PRE_PULL_IMAGE].render(image_tag=image_tag))
print("✅ Pre-pull image job generated")