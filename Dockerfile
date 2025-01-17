FROM python:3.10-slim

ENV VERSION=1.0

ARG UID=1001
ARG USER_NAME=forecast
ARG PIP_REQUIREMENTS_FILE="./requirements.txt"

ENV TZ="Europe/Moscow"

WORKDIR /home/${USER_NAME}
WORKDIR /csv
WORKDIR /app

RUN useradd ${USER_NAME} --user-group --uid ${UID} --home-dir /home/${USER_NAME} --base-dir /home/${USER_NAME} --shell /bin/sh \
    && chown -R ${USER_NAME}:${USER_NAME} /home/${USER_NAME} && chown -R ${USER_NAME}:${USER_NAME} /csv

RUN ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime

COPY ${PIP_REQUIREMENTS_FILE} requirements.txt

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY ./app /app
RUN chown -R ${USER_NAME}:${USER_NAME} /app

USER ${USER_NAME}

EXPOSE 8000
CMD uvicorn endpoint:app --host 0.0.0.0 --port 8000 --reload
