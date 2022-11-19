FROM ubuntu:22.04


# set a directory for the app
WORKDIR /usr/src/app

# install Python requirements
RUN apt update && apt-get upgrade -y
RUN apt install -y --no-install-recommends cron python3 python3-dev python3-venv
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Script file copied into container.
COPY imap_cleaner.py /usr/src/app


# Running commands for the startup of a container.
CMD python imap_cleaner.py True
