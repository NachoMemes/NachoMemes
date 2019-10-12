FROM ubuntu:18.04
RUN apt-get update \
    && apt-get -y install \
    python3 \
    python3-pip \
    git \
    sudo

RUN mkdir -p /app

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3","run.py"]
