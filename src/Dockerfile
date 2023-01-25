FROM python:3.10-slim-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
    && pip install --no-cache-dir --upgrade pip

WORKDIR /app
RUN mkdir -p -v /logs
RUN touch /logs/test.log
COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt
COPY . /app

COPY config/compose/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY config/compose/worker /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY config/compose/beat_start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./config/compose/flower /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

#EXPOSE 8000

#CMD ["python3", "main.py"]
