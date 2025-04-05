# app/Dockerfile

FROM python:3.13-bookworm

WORKDIR /bot

COPY bot/ /bot/

RUN apt-get update && apt-get install -y \
    build-essential \
    curl

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "economyBot.py"]
