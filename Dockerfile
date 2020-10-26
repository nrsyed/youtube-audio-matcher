FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y ffmpeg python3.8 python3-pip \
  && libpq-dev libmysqlclient-dev mysql-client-core-8.0 \
  && rm -rf /var/lib/apt/lists/*

COPY . /src
RUN cd /src \
  && pip3 install . \
  && cd .. \
  && rm -r src
