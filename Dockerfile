
FROM nginx:1.19

LABEL maintainer="masamitsu.murase@gmail.com" \
      version="1.3"

WORKDIR /home/developer

EXPOSE 3000

ENV FLASK_PORT=5000
ENV LFS_ROOT=/opt/home/data

COPY requirements.txt .
COPY prepare.sh .

RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-venv \
    && apt-get clean \
    && rm -f -r /var/lib/apt/lists/*
RUN /bin/bash prepare.sh

COPY nginx.conf.template .
COPY lfs_server.py .
COPY gunicorn.conf.py .
COPY run.sh .

CMD ["/bin/bash", "run.sh"]
