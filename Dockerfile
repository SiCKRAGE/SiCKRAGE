FROM python:3.7-alpine3.9
MAINTAINER echel0n <echel0n@sickrage.ca>

ARG SOURCE_COMMIT
ENV SOURCE_COMMIT $SOURCE_COMMIT

ENV TZ 'Canada/Pacific'
ENV WEB_ROOT ''

#RUN locale-gen en_US.UTF-8
#ENV LANG en_US.UTF-8
#ENV LANGUAGE en_US:en
#ENV LC_ALL en_US.UTF-8

COPY . /opt/sickrage/

RUN apk add --update --no-cache libffi-dev openssl-dev libxml2-dev libxslt-dev linux-headers build-base git tzdata unrar
RUN pip install -U pip setuptools
RUN pip install -r /opt/sickrage/requirements.txt

EXPOSE 8081
VOLUME /config /downloads /tv /anime

ENTRYPOINT python /opt/sickrage/SiCKRAGE.py --nolaunch --datadir /config