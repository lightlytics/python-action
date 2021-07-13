FROM python:3.9.5
ADD . /app
WORKDIR /app
ADD metadata.json /app/metadata.json
COPY metadata.json /app/metadata.json
ADD  plan.json /app/plan.json
COPY plan.json /app/plan.json
ADD requirements.txt /app/requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
ADD jsonapi.py /app/jsonapi.py
COPY jsonapi.py /app/jsonapi.py
ENV PYTHONPATH /app
CMD ["/app/jsonapi.py"]
