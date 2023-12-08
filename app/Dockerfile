FROM python:3.11

WORKDIR /app
ENV FLASK_APP=app

COPY requirements.txt ./

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y libgl1-mesa-glx
