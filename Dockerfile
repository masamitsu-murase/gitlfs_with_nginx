
FROM nginx:1.19

WORKDIR /home/developer

EXPOSE 3000

COPY nginx.conf.template .
COPY requirements.txt .
COPY lfs_server.py .
COPY prepare.sh .

RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-venv
RUN /bin/bash prepare.sh

COPY run.sh .

CMD ["/bin/bash", "run.sh"]
