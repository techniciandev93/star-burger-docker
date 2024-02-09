FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt update && \
    apt upgrade && \
    apt install -y python3-pip libpq-dev


COPY backend/requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

COPY backend/ .

RUN python manage.py collectstatic --no-input
