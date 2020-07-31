
FROM nginx:1.19

LABEL maintainer="masamitsu.murase@gmail.com" \
      version="1.5"

WORKDIR /home/developer

# Port 80 is exposed by nginx docker image.

ENV NGINX_PORT=80
ENV FLASK_PORT=5000
ENV LFS_ROOT=/opt/home/data
ENV SSL_CERTS_ROOT=/opt/home/ssl

COPY requirements.txt .
COPY prepare.sh .

RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-venv \
    && apt-get clean \
    && rm -f -r /var/lib/apt/lists/*
RUN /bin/bash prepare.sh

COPY nginx.conf.template .
COPY nginx_http.conf.template .
COPY nginx_https.conf.template .
COPY lfs_server.py .
COPY gunicorn.conf.py .
COPY run.sh .

CMD ["/bin/bash", "run.sh"]
