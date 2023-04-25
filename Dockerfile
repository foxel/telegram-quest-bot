FROM python:3.8-slim-buster

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
WORKDIR /app

COPY main.py config.yml /app/
COPY images/ /app/images/

CMD ["python", "main.py"]
