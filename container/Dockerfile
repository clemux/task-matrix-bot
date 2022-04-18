FROM python:3

WORKDIR /opt/taskbot

COPY taskbot/ taskbot/
COPY setup.cfg .
COPY pyproject.toml .
COPY taskrc /etc/taskrc

RUN apt update && apt upgrade -y
RUN apt install -y virtualenv libolm-dev taskwarrior

RUN virtualenv venv && venv/bin/pip install .

ENV TASKRC=/etc/taskrc
ENV TASKDATA=/data/task

ENTRYPOINT ["/opt/taskbot/venv/bin/taskbot"]