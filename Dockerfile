FROM ubuntu:22.04

# set a directory for the app
WORKDIR /usr/src/app

# install Python requirements
RUN apt update && apt-get upgrade -y
RUN apt install -y --no-install-recommends cron python3 python3-dev python3-venv
RUN python3 -m venv venv
ENV PATH="/usr/src/app/venv/bin:$PATH"
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Crontab file copied to cron.d directory.
COPY crontab.file /etc/cron.d/container_cronjob

# Script file copied into container.
COPY imap_cleaner.py /usr/src/app
COPY config.py /usr/src/app

# Running commands for the startup of a container.
CMD python imap_cleaner.py && chmod 644 /etc/cron.d/container_cronjob && cron && tail -f imap_cleaner.log
