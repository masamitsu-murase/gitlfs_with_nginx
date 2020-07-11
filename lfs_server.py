from datetime import datetime
from flask import abort, Flask, jsonify, request
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

app = Flask(__name__)
app.config["LFS_ROOT"] = "/opt/home/data" + "/repos"
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"].encode("utf-8")


def base_dir(repo, relative=False):
    if relative:
        return Path(repo)
    else:
        return Path(app.config["LFS_ROOT"]) / repo


def oid_path(repo, oid, relative=False):
    path = base_dir(repo,
                    relative=relative) / "objects" / oid[0:2] / oid[2:4] / oid
    return path


def oid_upload_url(base_url, repo, oid):
    return base_url + "upload/" + repo + "/" + oid


def oid_download_url(base_url, repo, oid):
    return base_url + "download/" + repo + "/" + oid


def hash_value(data):
    h = hashlib.blake2b(digest_size=64, key=app.config["SECRET_KEY"])
    h.update(data)
    return h.hexdigest()


def access_key(repo, req, expires_in=60 * 60):
    expires_at = int(time.time()) + expires_in
    obj = {"expires_at": expires_at}
    obj_str = json.dumps(obj)
    sig = hash_value(obj_str.encode("utf-8"))
    return sig, obj_str, expires_at


def verify_access_key(key, info_str, now):
    expected_key = hash_value(info_str.encode("utf-8"))
    if key != expected_key:
        return False
    info = json.loads(info_str)
    if info["expires_at"] < now:
        return False
    return True


def lfs_response(obj):
    return jsonify(obj), 200, {'Content-Type': 'application/vnd.git-lfs+json'}


def download(repo, req):
    if "basic" not in req.get("transfers", ["basic"]):
        abort(501)

    key, info, expires_at = access_key(repo, req)
    header = {"X-Access-Key": key, "X-Access-Info": info}
    expires_at_str = datetime.utcfromtimestamp(expires_at).isoformat() + "Z"
    base_url = request.url_root

    objects = []
    for obj in req["objects"]:
        oid = obj["oid"]
        path = oid_path(repo, oid)
        if path.is_file():
            url = oid_download_url(base_url, repo, oid)
            size = path.stat().st_size
            objects.append({
                "oid": oid,
                "size": size,
                "authenticated": True,
                "actions": {
                    "download": {
                        "href": url,
                        "header": header,
                        "expires_at": expires_at_str
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

    key, info, expires_at = access_key(repo, req)
    header = {"X-Access-Key": key, "X-Access-Info": info}
    expires_at_str = datetime.utcfromtimestamp(expires_at).isoformat() + "Z"
    base_url = request.url_root

    objects = []
    for obj in req["objects"]:
        oid = obj["oid"]
        url = oid_upload_url(base_url, repo, oid)
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

    if operation == "download":
        return download(repo, req)
    elif operation == "upload":
        return upload(repo, req)
    else:
        abort(400)


@app.route("/upload/<repo>/<oid>", methods=["PUT"])
def upload_file(repo, oid):
    body_filename = request.headers.get("X-File-Name", None)
    if not body_filename:
        abort(400)

    path = oid_path(repo, oid)
    if path.exists():
        return "", 200

    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(body_filename, path)
    return "", 200


@app.route("/download/<repo>/<oid>", methods=["GET"])
def download_file(repo, oid):
    path = oid_path(repo, oid)
    if not path.exists():
        abort(404)

    rel_path = oid_path(repo, oid, relative=True)
    url = "/repos/" + rel_path.as_posix()
    headers = {
        "X-Accel-Redirect": url,
        "Content-Type": "application/octet-stream"
    }

    return "", 200, headers


@app.route("/auth_request")
def auth_request():
    now = time.time()
    key = request.headers.get("X-Access-Key", None)
    info = request.headers.get("X-Access-Info", None)
    if key is None or info is None:
        abort(401)
    if not verify_access_key(key, info, now):
        abort(401)

    return "", 200


if __name__ == '__main__':
    port = 5000
    host = "localhost"
    app.run(host=host, port=port)
