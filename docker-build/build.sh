#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

IMAGE_NAME="frinx/$(poetry version --no-interaction | sed  's| |:|g')"
export IMAGE_NAME
DOCKERFILE="${DIR}/docker-build/Dockerfile"

docker build -t "${IMAGE_NAME}" -f "${DOCKERFILE}" "${DIR}"

