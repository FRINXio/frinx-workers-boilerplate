FROM python:3.11-alpine AS python-base

ARG TEMP_DIR

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_INSTALLER_PARALLEL=false \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base as builder-base
RUN apk add --no-cache \
        openssh-client \
        git

RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN pip3 install poetry==${POETRY_VERSION}

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./
COPY ${TEMP_DIR} "${PYSETUP_PATH}"

RUN --mount=type=ssh poetry install --no-interaction --no-ansi -vvv --only main

FROM python-base as production

RUN adduser -D frinx
USER frinx

COPY --from=builder-base --chown=frinx $PYSETUP_PATH $PYSETUP_PATH

WORKDIR "/home/app"
COPY --chown=frinx "main.py" .
COPY --chown=frinx devices ./devices

CMD ["python3", "-u", "main.py"]
