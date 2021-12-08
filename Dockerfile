FROM python:3.8

USER root

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update -y; apt-get upgrade -y; \
    apt-get install -y curl wget vim-tiny vim-athena jq git build-essential s3fs


# All imports needed for autodoc.
WORKDIR /usr/src/app
COPY . .
RUN bash -c "pip install wheel; pip install --no-cache-dir  -r ./requirements.txt; python setup.py build; python setup.py install -v"

# RUN bash -c "make install"

# WORKDIR /home
