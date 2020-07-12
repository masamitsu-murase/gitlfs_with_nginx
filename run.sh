
set -e

envsubst '$LFS_ROOT $EXTERNAL_PORT' < nginx.conf.template > /etc/nginx/nginx.conf
nginx -t
nginx

. venv/bin/activate
python lfs_server.py
