#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORK_DIR=$(mktemp -d -p "$DIR")
TEMP_DIR=$(basename "${WORK_DIR}")

IMAGE_NAME="frinx/$(poetry version --no-interaction | sed  's| |:|g')"
export IMAGE_NAME
DOCKERFILE="${DIR}/dockerfiles/Dockerfile"


if [[ ! "$WORK_DIR" || ! -d "$WORK_DIR" ]]; then
  echo "Could not create temp dir"
  exit 1
fi

# deletes the temp directory
function cleanup {
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

trap cleanup EXIT

cp -rL services "${WORK_DIR}/services"
tree "${WORK_DIR}/services"
export DOCKER_BUILDKIT=1
docker build -t "${IMAGE_NAME}" --ssh default -f "${DOCKERFILE}" "${DIR}" --build-arg TEMP_DIR="${TEMP_DIR}"

