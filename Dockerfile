# app/Dockerfile

FROM python:3.13-bookworm
LABEL org.opencontainers.image.source="https://github.com/chiefbacon/economy-bot"
LABEL org.opencontainers.image.description="Simple Economy Bot for Discord"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /bot

COPY bot/ /bot/

RUN apt-get update && apt-get install -y \
    build-essential \
    curl

RUN pip3 install -r requirements.txt

# Copy LICENSE and NOTICE into the image
COPY LICENSE /bot/LICENSE
COPY THIRD_PARTY.md /bot/THIRD_PARTY.md

ENTRYPOINT ["python3", "economyBot.py"]
