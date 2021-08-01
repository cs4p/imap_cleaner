FROM python:3.8-slim-buster

# set a directory for the app
WORKDIR /usr/src/app

# install Python requirements
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY main.py /usr/src/app
COPY config.py /usr/src/app
COPY run_me.py /usr/src/app

RUN cd /usr/src/app/
RUN chmod +x run_me.py

CMD python3 run_me.py