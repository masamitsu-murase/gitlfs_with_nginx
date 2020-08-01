
set -e

# Check whether SECRET_KEY is different from the default value.
if [ $SECRET_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" ]; then
    echo Set SECRET_KEY appropriately. 1>&2
    exit 1
fi

if [ $USE_HTTPS = "yes" ]; then
    export HTTP_OR_HTTPS_CONF="nginx_https.conf"
    mkdir -p /etc/nginx/certs
    cp ${SSL_CERTS_ROOT}/${SSL_CERTIFICATE} /etc/nginx/certs/server.pem
    cp ${SSL_CERTS_ROOT}/${SSL_CERTIFICATE_KEY} /etc/nginx/certs/server.key
else
    export HTTP_OR_HTTPS_CONF="nginx_http.conf"
fi

envsubst '$LFS_ROOT $EXTERNAL_PORT $FLASK_PORT $MAX_FILE_SIZE $HTTP_OR_HTTPS_CONF' < nginx.conf.template > /etc/nginx/nginx.conf
envsubst '$NGINX_PORT' < ${HTTP_OR_HTTPS_CONF}.template > /etc/nginx/${HTTP_OR_HTTPS_CONF}
nginx -t
nginx

. venv/bin/activate
gunicorn -c gunicorn.conf.py lfs_server:app
