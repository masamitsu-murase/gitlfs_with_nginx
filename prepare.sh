
set -e

# For HTTPS
curl https://ssl-config.mozilla.org/ffdhe2048.txt -o /etc/ssl/private/dhparam.txt

# For Flask
python3.7 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
