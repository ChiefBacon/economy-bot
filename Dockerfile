# app/Dockerfile

FROM python:3.13-alpine
LABEL org.opencontainers.image.source="https://github.com/chiefbacon/economy-bot"
LABEL org.opencontainers.image.description="Simple Economy Bot for Discord"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /bot

# Copy files to the image
COPY bot/ /bot/
COPY requirements.txt /bot/requirements.txt
COPY LICENSE /bot/LICENSE
COPY THIRD_PARTY.md /bot/THIRD_PARTY.md

RUN apk update && apk add \
    build-base \
    cmake \
    make \
    curl

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "economyBot.py"]
