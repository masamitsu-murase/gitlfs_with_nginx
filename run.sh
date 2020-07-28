
set -e

if [ $USE_HTTPS = "yes" ]; then
    export NGINX_PORT_AND_SSL_SETTING="$NGINX_PORT ssl"
else
    export NGINX_PORT_AND_SSL_SETTING="$NGINX_PORT"
fi

envsubst '$LFS_ROOT $EXTERNAL_PORT $FLASK_PORT $NGINX_PORT_AND_SSL_SETTING' < nginx.conf.template > /etc/nginx/nginx.conf
nginx -t
nginx

. venv/bin/activate
gunicorn -c gunicorn.conf.py lfs_server:app
