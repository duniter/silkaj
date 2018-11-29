# Install Silkaj with docker

This page is not meant to be a tutorial on docker, it just give some hints on deploying/using/developping silkaj with docker

## Developping with docker Debian oldstable

```
FROM debian:jessie

ARG DEBIAN_FRONTEND=noninteractive

# optionnel, passe en UTF-8 et en français
RUN apt-get update ; apt-get install -y locales
RUN sed -i 's/^# *\(fr_FR.UTF-8\)/\1/' /etc/locale.gen && locale-gen
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR:en
ENV LC_ALL fr_FR.UTF-8

RUN apt-get update -y ; apt-get install -y git python3-pip libssl-dev

RUN git clone https://git.duniter.org/clients/python/silkaj.git
WORKDIR /silkaj

RUN apt-get install -y build-essential libffi-dev
RUN pip3 install -e .
```

## Developping with docker Ubuntu 18.04
```
FROM ubuntu:bionic

ARG DEBIAN_FRONTEND=noninteractive

# optionnel, passe en UTF-8 et en français
RUN apt-get update ; apt-get install -y locales
RUN locale-gen fr_FR.UTF-8
ENV LANG fr_FR.UTF-8

RUN apt-get update -y ; apt-get install -y git python3-pip libssl-dev

RUN git clone https://git.duniter.org/clients/python/silkaj.git
WORKDIR /silkaj

RUN pip3 install -e .
```

## Using docker-compose

```
---
version: "3"
services:
  silkaj:
    build: .
#   volumes:
#   - "${SOURCE_PATH:-./}:/silkaj"
    command: bin/silkaj info
```

You can launch silkaj with the following command :
```
docker-compose run silkaj bin/silkaj <command>
```

You can mount your code in he /silkaj dir, the source needs to be 0.6.0 or greater.
