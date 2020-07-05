from datetime import datetime
from flask import abort, Flask, jsonify, request
from pathlib import Path
import secrets
import threading
import time

app = Flask(__name__)
app.config["LFS_ROOT"] = str(Path(__file__).absolute().parent / "repos")
app.config["ROOT_URL"] = "http://localhost:3000"


class KeyManager(object):
    def __init__(self):
        self._expires_at = {}
        self._lock = threading.Lock()

    def register_access_key(self, key, expires_at):
        with self._lock:
            self._expires_at[key] = expires_at
            print(self._expires_at)

    def is_valid_key(self, key, now):
        with self._lock:
            if key not in self._expires_at:
                return False
            return now < self._expires_at[key]


key_manager = KeyManager()


def base_dir(repo, relative=False):
    if relative:
        return Path(repo)
    else:
        return Path(app.config["LFS_ROOT"]) / repo


def oid_path(repo, oid, relative=False):
    path = base_dir(repo,
                    relative=relative) / "objects" / oid[0:2] / oid[2:4] / oid
    return path


def oid_url(repo, oid):
    # path = oid_path(repo, oid, relative=True)
    return request.url_root.rstrip("/") + "/upload_store/" + repo + "/" + oid


def access_key(repo, req, expires_in=60 * 60):
    expires_at = int(time.time()) + expires_in
    key = f"{secrets.token_hex()}"
    key_manager.register_access_key(key, expires_at)
    return key, expires_at


def lfs_response(obj):
    return jsonify(obj), 200, {'Content-Type': 'application/vnd.git-lfs+json'}


def download(repo, req):
    if "basic" not in req.get("transfers", ["basic"]):
        abort(501)

    key, expires_at = access_key(repo, req)
    header = {"Authorization": f"Key {key}"}

    objects = []
    for obj in req["objects"]:
        oid = obj["oid"]
        path = oid_path(repo, oid)
        if path.is_file():
            url = oid_url(repo, oid)
            size = path.stat().st_size
            objects.append({
                "oid": oid,
                "size": size,
                "authenticated": True,
                "actions": {
                    "download": {
                        "href": url,
                        "header": header,
                        "expires_at": expires_at
                    }
                }
            })
        else:
            objects.append({
                "oid": oid,
                "error": {
                    "code": 404,
                    "message": "Object does not exist"
                }
            })
    response = {"transfer": "basic", "objects": objects}
    return lfs_response(response)


def upload(repo, req):
    if "basic" not in req.get("transfers", ["basic"]):
        abort(501)

    key, expires_at = access_key(repo, req)
    header = {"Authorization": f"Key {key}"}
    expires_at_str = datetime.utcfromtimestamp(expires_at).isoformat() + "Z"

    objects = []
    for obj in req["objects"]:
        oid = obj["oid"]
        url = oid_url(repo, oid)
        size = obj["size"]
        objects.append({
            "oid": oid,
            "size": size,
            "authenticated": True,
            "actions": {
                "upload": {
                    "href": url,
                    "header": header,
                    "expires_at": expires_at_str
                }
            }
        })
    response = {"transfer": "basic", "objects": objects}
    return lfs_response(response)


@app.route("/lfs/<repo>/info/lfs/objects/batch", methods=["POST"])
def batch(repo):
    req = request.json
    operation = req["operation"]
    print(req)

    if operation == "download":
        return download(repo, req)
    elif operation == "upload":
        return upload(repo, req)
    else:
        abort(400)


@app.route("/upload_store/<repo>/<oid>", methods=["PUT"])
def upload_store(repo, oid):
    print(request.headers)
    print(repo, oid)
    if "X-FILE" in request.headers:
        pass
    else:
        print(request.get_data())
    abort(400)


@app.route("/nginx_auth_request")
def nginx_auth_request():
    now = time.time()
    key = request.headers.get("Authorization", None)
    if key is None or not key.startswith("Key "):
        abort(401)
    key_value = key[4:]
    if not key_manager.is_valid_key(key_value, now):
        abort(401)

    return "", 200


if __name__ == '__main__':
    port = 5000
    host = "localhost"
    app.run(host=host, port=port)
