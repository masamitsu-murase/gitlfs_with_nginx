
set -e

envsubst '$LFS_ROOT $EXTERNAL_PORT $FLASK_PORT' < nginx.conf.template > /etc/nginx/nginx.conf
nginx -t
nginx

. venv/bin/activate
gunicorn -c gunicorn.conf.py lfs_server:app
