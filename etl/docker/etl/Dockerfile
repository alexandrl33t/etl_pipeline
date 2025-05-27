# This Dockerfile uses multi-stage build to customize DEV and PROD images:
# https://docs.docker.com/develop/develop-images/multistage-build/

FROM python:3.9.7-slim-buster AS builder

ENV PATH="$PATH:/root/.poetry/bin"
# System deps:
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    wget \
    bash \
    build-essential \
    curl \
    gettext \
    git \
    libpq-dev

WORKDIR /code

# Setting up proper permissions:
RUN groupadd -r web && useradd -d /code -r -g web web \
  && chown web:web -R /code

# Copy only requirements, to cache them in docker layer
COPY --chown=web:web ./requirements.txt /code/

RUN pip install --upgrade pip && pip install -r requirements.txt

# Running as non-root user:
USER web

COPY --chown=web:web ./postgres_to_es /code
