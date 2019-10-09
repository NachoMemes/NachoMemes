FROM ubuntu:18.04
RUN apt-get update && apt-get install
RUN apt-get install ttf-mscorefonts-installer -y
RUN apt-get install python3 -y
RUN apt-get install python -y
RUN apt-get install git -y
RUN apt-get install python3-pip -y

RUN mkdir -p /app
WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3","run.py","branch=master"]