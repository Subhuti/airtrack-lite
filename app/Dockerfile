# AirTrack Beta v0.9 "Orville"

FROM python:3.11-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        mariadb-client \
        gcc \
        build-essential \
        libmariadb3 \
        libmariadb-dev \
        python3-dev \
        python3-venv \
        curl \
        tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy AirTrack app files
COPY . /app

# Set up Python virtual environment
RUN python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r requirements.txt

# Add MariaDB readiness script
COPY wait-for-mariadb.sh /wait-for-mariadb.sh
RUN chmod +x /wait-for-mariadb.sh

# Define default startup sequence
ENTRYPOINT ["/wait-for-mariadb.sh"]
CMD ["/venv/bin/python", "app.py"]

EXPOSE 5000
