FROM	python:3-slim
RUN	apt-get update \
	&& apt-get -yq install     git RUN mkdir -p /app
WORKDIR	/app
COPY	requirements.txt	/app/requirements.txt
RUN	pip3 install -r requirements.txt
COPY	.	/app
ENTRYPOINT	["python3","run.py"]
