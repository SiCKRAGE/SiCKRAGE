FROM python:2.7.15
MAINTAINER echel0n <echel0n@sickrage.ca>

# install app
COPY . /opt/sickrage/

RUN apt-get update && apt-get install -y libffi-dev libssl-dev python-psutil python-lxml python-cffi python-cryptography build-essential git tzdata
RUN pip install -U pip setuptools
RUN pip install -r /opt/sickrage/requirements.txt

# ports and volumes
EXPOSE 8081
VOLUME /config /downloads /tv /anime

ENTRYPOINT python /opt/sickrage/SiCKRAGE.py --nolaunch --datadir /config