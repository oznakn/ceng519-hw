FROM ubuntu:20.04

LABEL maintainer="ertanon@gmail.com"
LABEL version="0.1"
LABEL description="This is a Microsoft EVA development environment image based on Ubuntu 20.04"

ARG DEBIAN_FRONTEND=noninteractive

ENV LIBRARY_PATH="/lib:/usr/lib" \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_HOME="/opt/poetry" \
    PATH="/opt/poetry/bin:$PATH"

RUN apt update -yyq && apt upgrade -yyq \
    && apt install -yyq python3 python3-dev python3-pip python3-setuptools python3-venv software-properties-common nano vim rsync apt-utils build-essential git cmake curl wget libboost-all-dev libprotobuf-dev protobuf-compiler clang \
    && update-alternatives --install /usr/bin/cc cc /usr/bin/clang 100 \
    && update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++ 100 \
    && pip3 --no-cache-dir install --upgrade pip

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3 -

WORKDIR /development

RUN git clone --depth 1 --branch v3.6.4 https://github.com/microsoft/SEAL.git \
    && cd SEAL \
    && cmake -S . -B build -DSEAL_THROW_ON_TRANSPARENT_CIPHERTEXT=ON \
    && cmake --build build \
    && cmake --install build

RUN git clone --depth 1 https://github.com/microsoft/EVA.git \
    && cd EVA \
    && git submodule update --init --recursive \
    && cmake . \
    && make -j \
    && pip3 install -e ./python \
    && pip3 install -r examples/requirements.txt

RUN pip3 install networkx numpy
