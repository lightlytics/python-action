FROM python:3.9.5
COPY . /app
#
# COPY metadata.json /app/metadata.json
# COPY plan.json /app/plan.json

RUN pip3 install -r /app/requirements.txt

CMD ["python /app/jsonapi.py"]
