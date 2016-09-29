FROM ubuntu:16.04

MAINTAINER Marijan Beg <m.beg@soton.ac.uk>

RUN apt-get update -y && \
    apt-get install -y git python3-pip curl && \
    python3 -m pip install --upgrade pip pytest-cov codecov \
      matplotlib tornado ipython ipykernel

WORKDIR cd /usr/local/

RUN git clone https://github.com/joommf/discretisedfield.git