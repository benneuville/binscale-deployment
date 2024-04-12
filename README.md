# PER2023–045 - Type : Developpement
## Deployment, monitoring, and performance optimization of a microservices technology stack on Kafka, Kubernetes, GCP.
## Déploiement, monitoring et optimisation de performances d'une pile technologique de Micro services, sur Kafka, Kubernetes, GCP

### Authors of this repository
- [Antoine BUQUET](https://github.com/antoinebqt)
- [Benoit GAUDET](https://github.com/BenoitGAUDET38)
- [Ayoub IMAMI](https://github.com/AyoubIMAMI)
- [Mourad KARRAKCHOU](https://github.com/MouradKarrakchou)

---

### Technologies
- Docker
- Kubernetes (MiniKube, K3s)
- Kafka
- Ansible
- Prometheus
- Grafana
- Python
- Helm

---

### Project structure
- [ansible](https://github.com/antoinebqt/TER/tree/master/ansible) folder which contains the `.yaml` files to automatically deploy the application and its environment
- [kubernetes](https://github.com/antoinebqt/TER/tree/master/kubernetes) folder which contains the `.yaml` files used by the Ansible scripts to deploy all the Kubernetes ressources
- [scripts](https://github.com/antoinebqt/TER/tree/master/scripts) folder which contains the following `.sh` files:
  - `chmodAll.sh`: give the execution rights to all the scripts
  - `deploy-k3s-cluster.sh`: deploy a K3s cluster on a list of hosts
  - `deployEnv.sh`: deploy all the environment needed for the application
  - `launchExperience.sh`: launch the execution of the application, retrieve the data and generate the graphs in the [`python/output`](https://github.com/antoinebqt/TER/tree/master/python/output) folder
  - `mnk-requirements1.sh`: install Docker for Minikube
  - `mnk-requirements2.sh`: install Kubectl, Minikube, Helm, Python packages and Ansible

---
 
### First configuration with Minikube on a single, clean machine
NB: You must be in the root folder to use the scripts.

#### Requirements
- 18 CPU cores
- 18 GB of RAM

#### Steps

- Execute the following command in order to be able to **execute all the scripts**
```bash
chmod +x scripts/chmodAll.sh && scripts/chmodAll.sh
```
- **Install** Docker
```bash
scripts/mnk-requirements1.sh
```
- Once the previous script is done, **exit** the machine and **reconnect** to it in order to update the Docker users group, thus avoiding using the `sudo su` command everytime


- Install Kubectl, Minikube, Helm, Python packages and Ansible
```bash
scripts/mnk-requirements2.sh
```
- **Deploy** all the ressources
```bash
scripts/deployEnv.sh
```

- **Launch** the experience
```bash
scripts/launchExperience.sh
```

---

### Second configuration with K3s on a cluster of clean machines (Grid5000)

#### Requirements
- An account on Grid5000

#### Steps
- All information about Grid5000 can be found on [getting started](https://www.grid5000.fr/w/Getting_Started)
- Clone the project on your home directory on a site of Grid5000 (for exemple **sophia**)
- Get the number of hosts that you want for the K8s cluster
```bash
# Exemple of 2 nodes for 2 hours
oarsub -I -l host=2,walltime=2 -t deploy
kadeploy3 debian11-min
```
- Clone this project in your Grid5000 home directory
```bash
git clone https://github.com/antoinebqt/PER2023-045.git
```
- Modify the IP addresses in K3s/hosts.ini (only one master is allowed)
- Deploy the K3s cluster

NB: You must be in the root folder of the project to use the scripts.
```bash
cd PER2023-045
chmod +x scripts/chmodAll.sh && scripts/chmodAll.sh
vim k3s/hosts.ini
pip install ansible # not necessary if already installed
scripts/deploy-k3s-cluster.sh
```
- Connect to your master node
```bash
ssh root@<ip_address>
ssh root@<grid_node_name>
```
- Deploy the stack
```bash
cd ~/PER2023-045
scripts/deployEnv.sh
```
- Wait 10 minutes then launch the experience
```bash
scripts/launchExperience.sh
```
- Wait until the end of the experience
- Retrieve the experience data
```bash
# from your home Grid5000, not the master node
scp -r root@<ip_address>:~/PER2023-045/python/output ~
```
The data will be in your home directory
# Deployment
