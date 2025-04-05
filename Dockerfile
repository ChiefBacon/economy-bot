# app/Dockerfile

FROM python:3.13-bookworm

WORKDIR /bot

COPY bot/ /bot/

RUN apt-get update && apt-get install -y \
    build-essential \
    curl

RUN pip3 install -r requirements.txt

# Copy LICENSE and NOTICE into the image
COPY LICENSE /bot/LICENSE
COPY THIRD_PARTY_LICENSES.md /bot/THIRD_PARTY_LICENSES.md

ENTRYPOINT ["python3", "economyBot.py"]
