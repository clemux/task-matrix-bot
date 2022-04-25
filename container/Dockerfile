FROM python:3.9-slim-bullseye

WORKDIR /opt/taskbot

COPY taskbot/ taskbot/
COPY setup.cfg .
COPY pyproject.toml .
COPY taskrc /etc/taskrc

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libolm-dev libolm3 taskwarrior python3-dev gcc

RUN python -m venv venv && venv/bin/pip install .

RUN apt-get remove -y python3-dev libolm-dev gcc && apt-get autoremove -y

ENV TASKRC=/etc/taskrc
ENV TASKDATA=/data/task

ENTRYPOINT ["/opt/taskbot/venv/bin/taskbot"]