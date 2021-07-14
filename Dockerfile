FROM python:3.9.5
COPY . /app

COPY metadata.json /app/metadata.json
COPY plan.json /app/plan.json

WORKDIR /app
RUN pip3 install -r requirements.txt
ENV PYTHONPATH /app
CMD ["python /app/jsonapi.py"]
