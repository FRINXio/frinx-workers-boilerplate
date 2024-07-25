# frinx-workers-boilerplate

- helm-chart:   Frinx Machine installation scripts
- worker:   Python worker project

## Frinx Machine installation

### Cluster setup

Start minikube with recommended settings
```bash
minikube start --cpus=max --memory=24G --addons=ingress
```

Get minikube ip

```bash
minikube ip

192.168.49.2
```

Add to your /etc/hosts. Change to your minikube ip

```bash
#/etc/hosts
192.168.49.2 krakend.127.0.0.1.nip.io workflow-manager.127.0.0.1.nip.io
```

```bash
kubectl create namespace frinx
```

### Helm Charts installation

Create a kubernetes Docker registry secret for pulling images from private registry:

```bash
# PLACEHOLDERS must be replaced with user credentials
kubectl create secret -n frinx docker-registry regcred \
    --docker-server="https://index.docker.io/v1/" \
    --docker-username="<PLACEHOLDER>" \
    --docker-password="<PLACEHOLDER>"
```

For more info about accessing private images, visit [Download Frinx Uniconfig](https://docs.frinx.io/frinx-uniconfig/getting-started/#download-frinx-uniconfig)


Frinx Machine operators
```bash
helm dependency build ./helm-charts/frinx-machine-operators
helm upgrade --install -n frinx frinx-machine-operators ./helm-charts/frinx-machine-operators
```

Frinx Machine
```bash
helm dependency build ./helm-charts/frinx-machine
helm upgrade --install -n frinx frinx-machine ./helm-charts/frinx-machine
```

In case, you want to work with simulated devices, run sample-topology as well

Sample Topology
```bash
helm dependency build ./helm-charts/sample-topology
helm upgrade --install -n frinx sample-topology ./helm-charts/sample-topology
```

### Custom Worker customization

Change image repositor and tag to address your image

```bash
# helm-charts/custom-worker/values.yaml
  image:
    repository: frinx/frinx-demo-workflows
    tag: "6.0.0"
```

You can import your custom image via:

```bash
minikube image load your/image:tag
```

## Custom worker setup

### Create project

```bash
poetry env use python3.10
poetry install
```

### Start project

```bash
poetry run python3 main.py
```

### Configure rbac

```bash
# .env
# CONFIGURE CONDUCTOR CLIENT URL
CONDUCTOR_URL_BASE=http://workflow-manager.127.0.0.1.nip.io/api
# USE KRAKEND ENDPOINTS To ACCESS API  
SCHELLAR_URL_BASE=http://krakend.127.0.0.1.nip.io/api/schedule
UNICONFIG_URL_BASE=http://krakend.127.0.0.1.nip.io/api/uniconfig
INVENTORY_URL_BASE=http://krakend.127.0.0.1.nip.io/api/inventory
RESOURCE_MANAGER_URL_BASE=http://krakend.127.0.0.1.nip.io/api/resource
KRAKEND_URL_BASE=http://krakend.127.0.0.1.nip.io
UNICONFIG_ZONE_URL_TEMPLATE=http://krakend.127.0.0.1.nip.io/api/{uc}
# WORKER RBAC
X_AUTH_USER_GROUP=FRINXio
```

### Configure Ingress for services

```yaml

frinx-machine:
  krakend:
    ingress:
      enabled: true
      className: nginx
      annotations:
        nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
        nginx.ingress.kubernetes.io/proxy-connect-timeout: "3600"
        nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
        nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
      hosts:
        - host: krakend.127.0.0.1.nip.io
          paths:
            - path: "/"
              pathType: ImplementationSpecific

  workflow-manager:
    ingress:
      enabled: true
      hosts:
        - host: workflow-manager.127.0.0.1.nip.io
          paths:
            - path: "/"
              pathType: ImplementationSpecific
      schellarHosts:
        - host: workflow-manager-schellar.127.0.0.1.nip.io
          paths:
            - path: "/"
              pathType: ImplementationSpecific
```

