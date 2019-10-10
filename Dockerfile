FROM ubuntu:18.04
RUN apt-get update \
    && apt-get -y install \
    python3 \
    python3-pip \
    git \
    sudo
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | sudo debconf-set-selections
RUN sudo apt-get install ttf-mscorefonts-installer -y
RUN rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3","run.py"]