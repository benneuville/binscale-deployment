## Deployment, monitoring, and performance optimization of a microservices technology stack on Kafka, Kubernetes.
## Déploiement, monitoring et optimisation de performances d'une pile technologique de Micro services, sur Kafka, Kubernetes.

### Author of this repository
[Fatima Zahrae LAAZIZ](https://github.com/fatimazahraelaaziz)


---

### Technologies
- Docker
- Kubernetes (MiniKube)
- Kafka
- Ansible
- Prometheus
- Grafana
- Python
- Helm

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
- **PS: In order to reset ** the machine
```bash
scripts/resetCluster.sh
```
