## Deployment, monitoring, and performance optimization of a microservices technology stack on Kafka, Kubernetes.
## Déploiement, monitoring et optimisation de performances d'une pile technologique de Micro services, sur Kafka, Kubernetes.

---

### Technologies
- Docker
- Kubernetes (MiniKube)
- Helm
- Kafka
- Ansible
- Prometheus
- Grafana
- Python
- ElasticSearch
- Kibana

---

### Project structure
- [ansible](https://github.com/fatimazahraelaaziz/Deployment/tree/master/ansible) folder which contains the `.yaml` files to automatically deploy the application and its environment
- [kubernetes](https://github.com/fatimazahraelaaziz/Deployment/tree/master/kubernetes) folder which contains the `.yaml` files used by the Ansible scripts to deploy all the Kubernetes ressources
- [scripts](https://github.com/fatimazahraelaaziz/Deployment/tree/master/scripts) folder which contains the following `.sh` files:
  - `chmodAll.sh`: give the execution rights to all the scripts
  - `deployEnv.sh`: deploy all the environment needed for the application
  - `launchExperience.sh`: launch the execution of the application, retrieve the data and generate the graphs in the [`python/output`](https://github.com/fatimazahraelaaziz/Deployment/tree/master/python/output) folder
  - `mnk-requirements1.sh`: install Docker for Minikube
  - `mnk-requirements2.sh`: install Kubectl, Minikube, Helm, Python packages and Ansible

---

### Link to Experience
[Experience Repository](https://github.com/fatimazahraelaaziz/Experience/tree/main)

 
### First configuration with Minikube on a single, clean machine
NB: You must be in the root folder to use the scripts.

#### Requirements
- 18 CPU cores
- 18 GB of RAM

#### Steps Multi-nodes cluster
- Change the name of your host (master-node, worker01,...)
```bash
sudo hostnamectl set-hostname <hostname>
bash
```
- Add all hostnames in the `/etc/hosts` file (ex: `172.16.39.3 master-node`)
```bash
nano /etc/hosts
```
- **For Master** (it could take long time):
```bash
./scripts/multinode-master.sh
```
- **For Workers**:
```bash
./scripts/multinode-worker.sh
```
*On the master, you will take the last command printed in green and copy-paste it in workers. Or, in the master, use* `kubeadm token create --print-join-command` *to get the* `sudo kubeadm join [master-node-ip]:6443 --token [token] --discovery-token-ca-cert-hash sha256:[hash]` *to join the cluster as a node.*

- **Deploy** all the ressources
```bash
scripts/deployEnv.sh
```

- **Launch** the experience
```bash
scripts/launchExperience.sh
```
- **PS: Reset (for Master)** the cluster
```bash
scripts/multinode-resetcluster.sh
```
- **PS2: Reset Worker**
```bash
kubeadm reset -f
```
*Note that you have to reset the cluster, you have to reset master and workers, and do the* `kubeadm join` *command on workers seen before*


#### Steps Minikube

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
- **PS: In order to reset** the machine
```bash
scripts/resetCluster.sh
```
### Steps