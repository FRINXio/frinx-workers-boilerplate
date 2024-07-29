FROM python:3.11-alpine AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_INSTALLER_PARALLEL=false \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base as builder-base

RUN pip3 install poetry==${POETRY_VERSION}

WORKDIR $PYSETUP_PATH
COPY poetry.lock $PYSETUP_PATH
COPY pyproject.toml $PYSETUP_PATH/
COPY app $PYSETUP_PATH
COPY README.md $PYSETUP_PATH

RUN poetry install --no-interaction --no-ansi -vvv --only main --no-root

FROM python-base as production

RUN adduser -D frinx
USER frinx

COPY --from=builder-base --chown=frinx $PYSETUP_PATH $PYSETUP_PATH

WORKDIR "/home/app"
COPY --chown=frinx "main.py" .
COPY --chown=frinx "app" .

CMD ["python3", "-u", "main.py"]
