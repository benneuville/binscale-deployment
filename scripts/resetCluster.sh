minikube delete
minikube start --cpus=18 --memory=18g --insecure-registry 134.59.129.189:5000 --kubernetes-version v1.34.0
minikube mount python/input:/var/log/experiments/ &