# Deployment, monitoring, and performance optimization of a microservices technology stack on Kafka, Kubernetes on Grid5000 (and locally on Minicube).

The goal of this repository is to experiment the Bin Pack autoscaler solution in a Multinode Cluster with Grid5000.
---

## Technologies
- Docker
- Kubernetes (MiniKube or Kubeadm & Kubelet)
- Helm
- Kafka
- Ansible
- Prometheus
- Grafana
- Python
- Kibana
- NFS server (for multinode solution)

---

## Project structure

- [/ansible](https://github.com/benneuville/binscale-deployment/tree/no_elastic/ansible) folder which contains the `.yaml` files to automatically deploy the application and its environment
- [/kubernetes](https://github.com/benneuville/binscale-deployment/tree/no_elastic/kubernetes) folder which contains the `.yaml` files used by the Ansible scripts to deploy all the Kubernetes ressources
- [/scripts](https://github.com/benneuville/binscale-deployment/tree/no_elastic/scripts) folder which contains the following `.sh` files

### MULTI-NODES cluster scripts
- `multinode-master.sh`: deploy master-node
- `multinode-worker.sh`: deploy worker
- `multinode-launchExperience.sh`: launch experience on master-node
- `multinode-resetcluster.sh`: reset cluster on master-node

Other scripts could be common to master and workers deployment, and are called in `multinode-master.sh` and `multinode-worker.sh`
- `mtnd-requierements.sh` : common requierements between master and workers
- `mtnd-experience-requierements.sh` : requierements for experience (on master) Ansible (and package requierements), Helm, , JQ commands, Python
- `mtnd-docker.sh` : install Docker
- `mtnd-k8s.sh` : install kubernetes, kubeadm & kubelet
- `mtnd-nfs-master.sh` : install, deploy & configure NFS Server
- `mtnd-nfs-worker.sh` : install NFS utils & configure mount

### MINIKUBE scripts
- `chmodAll.sh`: give the execution rights to all the scripts
- `deployEnv.sh`: deploy all the environment needed for the application
- `launchExperience.sh`: launch the execution of the application, retrieve the data and generate the graphs in the [`python/output`](https://github.com/fatimazahraelaaziz/Deployment/tree/master/python/output) folder
- `mnk-requirements1.sh`: install Docker for Minikube
- `mnk-requirements2.sh`: install Kubectl, Minikube, Helm, Python packages and Ansible

---

## Link to Experience
* [Source Experience Repository](https://github.com/fatimazahraelaaziz/Experience/tree/main)
* [Experience Repository](https://github.com/benneuville/binscale-experience/tree/no_elastic) for this repository

 
## First configuration with Minikube on a single, clean machine
NB: You must be in the root folder to use the scripts.

### Requirements
- 18 CPU cores
- 18 GB of RAM


### Grid 5000
Here are some instructions on useful procedures and commands on [Grid5000](https://www.grid5000.fr/) and is based on the [Getting Started](https://www.grid5000.fr/w/Getting_Started) section
#### Create an account
Refer to [Get an account](https://www.grid5000.fr/w/Grid5000:Get_an_account) section of the website

#### Access to Grid5000
```bash
ssh <login>@access.grid5000.fr
```
#### Connect to a frontend site
```bash
ssh <site> # grenoble
```
*You can choose along the list of sites [here](https://www.grid5000.fr/w/Grid5000:Network#Grid'5000_sites_networks). For multiples nodes cluster and to respect the [Usage Policy](https://www.grid5000.fr/w/Grid5000:UsagePolicy),* ***Grenoble is advised***

#### Deploy a job with your environment
On a frontend site, to allocate a job :
  ```bash
  oarsub -I -t deploy -l host=1,walltime=8
  ```
  You will get an output like
  ```bash
  # Filtering out exotic resources (servan, drac, yeti, troll).
  OAR_JOB_ID=<job_id>
  # Interactive mode: waiting...
  # Starting...
  ```
  *More explainations [here](https://www.grid5000.fr/w/Getting_Started#Reserving_resources_with_OAR:_the_basics) to understand how to use OAR commands*

And to deploy an environment in the job :
  ```bash
  kadeploy3 ubuntu2204-min
  ```
  *More explainations [here](https://www.grid5000.fr/w/Getting_Started#Deploying_your_nodes_to_get_root_access_and_create_your_own_experimental_environment) to understand how kadeploy and OAR work*

#### Delete a job
On a frontend site or access site
```bash
curl -i -X DELETE https://api.grid5000.fr/stable/sites/<site>/jobs/<job_id>
```
Refer to [job deletion](https://www.grid5000.fr/w/API_tutorial#Job_deletion) API Tutorial

#### Extract data results

  **On your external machine**, setup your `.ssh/config` with :

  ```xml
  Host g5k
    User <login>
    Hostname access.grid5000.fr
    ForwardAgent no

  Host grenoble.g5k
    User <login>
    ProxyCommand ssh g5k -W grenoble:%p
    ForwardAgent no
  ```
  *Note : you can modify `grenoble` by another site*

**On frontend** (like grenoble), use *scp commands* to get image results
```bash
scp root@<master-node>:binscale-deployment/python/input/*.png ./public/result/
# example : scp root@dahu-22:binscale-deployment/python/input/*.png ./public/result/
```

Then, **on your external machine**, use *scp commands*
```bash
scp <site>.g5k:public/result/*.png .
# example : scp grenoble.g5k:public/result/*.png .
```

#### Reset Cluster data
To avoid data blend
- **On master-node**
  ```bash
  rm python/input/*.*
  ```
- **On frontend**
  ```bash
  rm /public/result/*
  ```

### Steps Multi-nodes cluster
- Execution scripts
```bash
chmod +x scripts/*
```
- Change the name of your host (master-node, worker01,...)
```bash
sudo hostnamectl set-hostname <hostname>
bash
```
*Note that the master need to be named **master-node***
- Add all hostnames in the `/etc/hosts` file (ex: `172.16.39.3 master-node`)
```bash
nano /etc/hosts
```
- **Deploy**

    **For 👑Master** (it could take long time)
    ```bash
    ./scripts/multinode-master.sh
    ```
    **For 🦺Workers**
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
scripts/multinode-launchExperience.sh
```
- **PS: Reset the cluster**

    **For 👑Master**
    ```bash
    scripts/multinode-resetcluster.sh
    ```
    **For 🦺Workers**
    ```bash
    kubeadm reset -f
    ```
    *Note that you have to reset the cluster, you have to reset master and workers, and do the* `kubeadm join` *command on workers seen before*

---
### Steps Minikube

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