FROM alpine:latest
MAINTAINER echel0n <echel0n@sickrage.ca>

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="Version:- ${VERSION} Build-date:- ${BUILD_DATE}"

# install app
COPY . /opt/sickrage/

# bash is better than sh
RUN apk upgrade && apk add bash
SHELL ["bin/bash", "-c"]

# install deps, then remove build deps
# can find missing deps here: https://pkgs.alpinelinux.org/contents
RUN set -o pipefail && \
    apk add \
        gcc \
        libffi-dev \
        libxml2-dev \
        libxslt-dev \
        linux-headers \
        musl-dev \
        openssl-dev \
        py2-pip \
        python2-dev \
    && \
    ln -s /usr/include/libxml2/libxml /usr/include/libxml && \
    pip install -U pip setuptools && \
    pip install -r /opt/sickrage/requirements.txt && \
    apk del \
        gcc \
        linux-headers \
        python2-dev

# ports and volumes
EXPOSE 8081
VOLUME /anime /config /downloads /tv

ENTRYPOINT python2 /opt/sickrage/SiCKRAGE.py --nolaunch --datadir /config
