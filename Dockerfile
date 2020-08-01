FROM python:3.8-alpine3.12
MAINTAINER echel0n <echel0n@sickrage.ca>

ARG SOURCE_COMMIT
ENV SOURCE_COMMIT $SOURCE_COMMIT
ENV PYTHONIOENCODING="UTF-8"
ENV TZ 'Canada/Pacific'

COPY . /opt/sickrage/

RUN apk add --update --no-cache libffi-dev openssl-dev libxml2-dev libxslt-dev linux-headers build-base git tzdata unrar
RUN pip install -U pip setuptools
RUN pip install -r /opt/sickrage/requirements.txt

EXPOSE 8081
VOLUME /config /downloads /tv /anime

ENTRYPOINT ["python", "/opt/sickrage/SiCKRAGE.py"]
CMD ["--nolaunch", "--datadir=/config"]