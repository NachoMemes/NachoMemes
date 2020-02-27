	
FROM	python:3-slim
RUN	export DEBIAN_FRONTEND=noninteractive \
	&& apt update -q < /dev/null > /dev/null \
	&& apt install -yq --no-install-recommends build-essential git < /dev/null > /dev/null \
	&& rm -rf /var/lib/apt/lists/*
COPY	requirements.txt	/app/requirements.txt
WORKDIR	/app
RUN	pip3 -q install -r requirements.txt
COPY	.	/app
ENTRYPOINT	["python3", "-m", "nachomemes.bot"]
