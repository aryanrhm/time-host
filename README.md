# Time Host Application
This repository creates a simple Django app that responds to an HTTP GET request and returns:
- Timestamp
- Hostname
Then with the help of Docker, Jenkins, Helm Chart, and ArgoCD Image Updater creates a CICD pipeline on a Kubernetes cluster which is deployed with the use of Kind cluster. At the end there would be an application in time-host namespace with its deployment, service, and ingress installed.

>Notes: 
>To decrease the size of image, the alpine is used as the base image.
>With the use of django-promethus, the metrics of the service could be scraped at the 8000 port and /metrics path. We can collect these metrics by Prometheus server. 

### Prerequisites
Before you can use this repository, you need to have the following:

- 2 Ubuntu 22.04 servers
	- main-server which have git, Docker, Ansible, Helm, Kubectl installed on it. Then we should install Kind cluster,  and run Ansible playbook with an ubuntu user which will install Jenkins on jenkins-server
	- jenkins-server, which the ssh-key of the ubuntu user on main-server is added on it. Because we want to run the Ansible playbooks from the main-server to install Jenkins and JCasC on this node.

### Installation on the main-server
The Kind application could be installed with the following commands:
```
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```
Then you can create the Kind cluster with the following command:
```
kind create cluster --config kind-config.yaml
```
You can find kind-config.yaml in the kubernetes directory. It is configured to bind a port (30001) on the host to a port (30001) on the Kind containers to define NodePort services inside the Kind cluster and can use them on the host network. 

Now we can install nginx ingress for the cluster:
```
skubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.44.0/deploy/static/provider/cloud/deploy.yaml
```
Then install ArgoCD to handle the CD part of our CICD pipeline.
```
kubectl create namespace argocd 
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```
Then forward the port of ArgoCD service to access its GUI:
```
kubectl port-forward svc/argocd-server -n argocd 30002:8080 --address 0.0.0.0
```

Now we can add the IP of the jenkins-server to Ansible inventory file and add the Docker Hub credentials to the secrets.yml file like this:
```
DOCKER_HUB_TOKEN: XXXX
DOCKER_HUB_USER: XXXX
```

And run the Ansible Playbook to install Jenkins on the jenkins-server, configure the JCasC on it, and have the time-host pipeline on the Jenkins server ready to run. Actually, we do not need to configure the Jenkins through its GUI and the pipeline is read from the Jenkinsfile in the myproject path.
Because the Jenkins Server does not have a Public IP, we cannot add the GitHub Hook to trigger the pipeline after the commits in GitHub. So we can use the Poll SCM option of the Jenkins to check the commits on the GitHub repository every 10 minutes.

---

Now the pipeline which has 3 stages can run. In the first stage (preparation) the Commit ID would be obtained to use in the tag of the Image, second the test would run, and finally the docker image would be created and pushed to the Docker Hub.
Now the image is updated, so the application deployment should be updated with the new image.
We can use the ArgoCD Image Updater, which checks the Docker Hub for the changes of the image, and updates the git repository with the new image (or tag).
In this repo we use a helm chart named base-chart to create the ArgoCD application with that. The configuration of this application is kubernetes/argocd/time-host-app.yaml which should be applied in your Kubernetes Cluster.
This file will configure the time-host-app and also the Image Updater for this app. To use the Image Updater we should add a secret for our GitHub repository and a Secret for the Docker Hub. An example secret file for the GitHub is in kubernetes/argocd/git-secret.yaml path and the username and password fields should be filled with your GitHub User Name and your Personal Access Tokens. The secret for Docker Registry could be created like this:
```
kubectl -n argocd create secret docker-registry docker-hub-secret \
    --docker-server=registry-1.docker.io \
    --docker-username=<user-name> \
    --docker-password=<user-token> 
```
Now that our Image Updater is configured, after each successful run of our pipeline in Jenkins, the GitHub repository would be updated with the new Image or new Tag, then the Deployment updates automatically with the new Image.

This is the log of Jenkins pipeline after successful run:

![Pasted image 20230701040650](https://github.com/aryanrhm/time-host/assets/84747328/eeb22352-99df-421d-aee6-9d6a670cf07f)


Now we can see that the Image Updater changed the GitHub Repository:

![Untitled](https://github.com/aryanrhm/time-host/assets/84747328/56fb7484-11a6-4c62-958c-3da9e5da598d)




And the Deployment is changed by ArgoCD either:

![Pasted image 20230701040946](https://github.com/aryanrhm/time-host/assets/84747328/22b96675-8d52-4575-97c9-a33d66762613)

We can also see these changes in the logs of the image updater in our Kubernetes Cluster:
```
time="2023-07-01T02:09:17Z" level=debug msg="target parameters: image-spec= image-name=image.repository, image-tag=image.tag" application=time-host image=registry-1.docker.io/aryanrhm/time_host
time="2023-07-01T02:09:17Z" level=debug msg="Image 'registry-1.docker.io/aryanrhm/time_host:939f281' already on latest allowed version" alias=myalias application=time-host image_name=aryanrhm/time_host image_tag=939f281 registry=registry-1.docker.io
time="2023-07-01T02:09:17Z" level=info msg="Processing results: applications=1 images_considered=1 images_skipped=0 images_updated=0 errors=0"
```


And the result of HTTP Get request to the application:
```
curl 127.0.0.1:30001
{"timestamp": "2023-07-01 02:30:26", "hostname": "time-host-deployment-7d5d7f55c4-sfb9t"}
```
