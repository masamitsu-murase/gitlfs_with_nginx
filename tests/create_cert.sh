
cd `dirname $0`

mkdir -p cert
cd cert

OPENSSL=openssl
$OPENSSL genrsa -out server.key 2048
$OPENSSL req -new -key server.key -out server.csr -subj "/C=JP/ST=Tokyo/L=Tokyo/CN=localhost"
$OPENSSL x509 -in server.csr -days 36500 -req -signkey server.key -out server.pem
