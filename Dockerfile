
FROM nginx:1.19

WORKDIR /home/developer

ENV SECRET_KEY 10a2381ab1048a8431bb478563b8e28e763facbaeba8824f9b7

COPY nginx.conf .
RUN cp nginx.conf /etc/nginx/nginx.conf

COPY requirements.txt .
COPY lfs_server.py .
COPY prepare.sh .

RUN apt-get update && apt-get install -y \
        python3.7 \
        python3-venv
RUN bash prepare.sh

COPY run.sh .
