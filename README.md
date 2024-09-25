# frinx-workers-boilerplate

This repository provides an easy setup for the [workflow manager worker](https://docs.frinx.io/frinx-workflow-manager/python-sdk/).

### Prerequisities

Before you begin, ensure you have the following tools installed:

- `python`: Version 3.10 or higher
- `poetry`: Python packaging and dependency management tool
- `frinx-machine`: Follow the instructions at [Frinx Machine GitHub](https://github.com/FRINXio/gitops-boilerplate)
- `mirrord`: Install Mirrord to your IDE/ENV and set kubeconfig context to right cluster/namespace.

## Quick Start

Ensure you are using Python version 3.10 or higher. 
Set up your environment and install dependencies with `poetry`:

```bash
# Use python version 3.10 or higher
poetry env use python3.10
poetry install
```

### Start project

Use a config/env_local.template file and configure it as follows:

```bash
# WORKER RBAC
X_AUTH_USER_GROUP=FRINXio
```

Export the environment variables and run the main script:

```bash
export $(cat config/env_local.template | sed -e /^$/d -e /^#/d | xargs)
mirrord exec poetry run python3 main.py --target targetless
```
