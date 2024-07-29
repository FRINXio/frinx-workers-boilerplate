# frinx-workers-boilerplate

This repository provides an easy setup for the [workflow manager worker](https://docs.frinx.io/frinx-workflow-manager/python-sdk/).

### Prerequisities

Before you begin, ensure you have the following tools installed:

- `python`: Version 3.10 or higher
- `poetry`: Python packaging and dependency management tool
- `frinx-machine`: Follow the instructions at [Frinx Machine GitHub](https://github.com/FRINXio/gitops-boilerplate)

## Quick Start

Ensure you are using Python version 3.10 or higher. 
Set up your environment and install dependencies with `poetry`:

```bash
# Use python version 3.10 or higher
poetry env use python3.10
poetry install
```

### Start project

Use Krakend and worker ingress for local development. 
Override default SDK environment variables with your own. 
Note that these environment variables should not be used in a Kubernetes deployment.

Use a config/env_local.template file and configure it as follows:

```bash
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

Export the environment variables and run the main script:

```bash
export $(cat config/env_local.template | sed -e /^$/d -e /^#/d | xargs)
poetry run python3 main.py
```
