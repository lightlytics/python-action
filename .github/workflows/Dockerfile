FROM python:3.9.5
ADD . /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
ADD jsonapi.py /app/jsonapi.py
COPY jsonapi.py /app/jsonapi.py
ENV PYTHONPATH /app
CMD ["/app/jsonapi.py"]
