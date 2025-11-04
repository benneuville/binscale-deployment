from jinja2 import Template
import yaml

WORLOAD = "workload"
LATENCY = "latency"
CONTROLLER = "controller"

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
    templates["kafka-topic"] = Template(f.read())

## Load graph
with open("experience/generator/graph.yaml") as f:
    graph = yaml.safe_load(f)

### Generate deployment files
edges = []
nodes = {}

for node in graph["nodes"]:
    node["targets"] = []
    nodes[node["id"]] = node

for edge in graph["edges"]:
    tmp_edge = {
        "from": edge["from"],
        "to": edge["to"],
        "weight": edge.get("weight", 1),
        "partitions": edge.get("partitions", 10),
        "topic_name": f"topic-{edge['from']}-to-{edge['to']}"
    }
    edge_check(tmp_edge, nodes)
    
    nodes[tmp_edge["to"]]["params"]["topic_name"] = tmp_edge["topic_name"]

    if is_workload_node(nodes[tmp_edge["from"]]["type"]):
        nodes[tmp_edge["from"]]["params"]["partition_weights"] = ','.join(["1"] * tmp_edge["partitions"])
        nodes[tmp_edge["from"]]["params"]["topic_name"] = tmp_edge["topic_name"]
    else:
        nodes[tmp_edge["from"]]["targets"].append({ "topic_name": tmp_edge["topic_name"], "ratio": tmp_edge["weight"] })

    edges.append(tmp_edge)



print("🚂 Generating Kafka topics...")
edges_topic_gen = []
for edge in edges:
    edges_topic_gen.append(templates["kafka-topic"].render(edge))

# Output all topics in one file in "/generated/kafka-topics.yaml"
with open("experience/generated/kafka-topics.yaml", "w") as f:
    f.write("\n---\n".join(edges_topic_gen))

print("✅ Kafka topics generated")

print("🚂 Generating Service nodes...")
nodes_service_gen = []
for node in [v for v in nodes.values() if v["type"] == LATENCY]:
    nodes_service_gen.append(templates[node["type"]].render(node=node))
# Output all service nodes in one file in "/generated/latency.yaml"
with open("experience/generated/latency.yaml", "w") as f:
    f.write("\n---\n".join(nodes_service_gen))

print("✅ Service nodes generated")

print("🚂 Generating Workload nodes...")
nodes_workload_gen = []
for node in [v for v in nodes.values() if v["type"] == WORLOAD]:
    nodes_workload_gen.append(templates[node["type"]].render(node=node))
# Output all workload nodes in one file in "/generated/workload.yaml"
with open("experience/generated/workload.yaml", "w") as f:
    f.write("\n---\n".join(nodes_workload_gen))

print("✅ Workload nodes generated")

