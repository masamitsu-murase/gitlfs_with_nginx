
FROM nginx:1.19

WORKDIR /home/developer

EXPOSE 3000

COPY requirements.txt .
COPY prepare.sh .

RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-venv
RUN /bin/bash prepare.sh

COPY nginx.conf.template .
COPY lfs_server.py .
COPY run.sh .

CMD ["/bin/bash", "run.sh"]
