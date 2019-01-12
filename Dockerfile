FROM python:2.7.15-alpine3.8
MAINTAINER echel0n <echel0n@sickrage.ca>

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="Version:- ${VERSION} Build-date:- ${BUILD_DATE}"

# install app
COPY . /opt/sickrage/

RUN apk add --no-cache build-base git
RUN pip install -U pip setuptools
RUN pip install -r /opt/sickrage/requirements.txt

# ports and volumes
EXPOSE 8081
VOLUME /config /downloads /tv /anime

ENTRYPOINT python /opt/sickrage/SiCKRAGE.py --nolaunch --datadir /config