from datetime import datetime
from flask import abort, Flask, jsonify, request
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time

app = Flask(__name__)
LFS_ROOT_REPOS = Path(os.environ["LFS_ROOT"]) / "repos"
SECRET_KEY = os.environ["SECRET_KEY"].encode("utf-8")
if len(SECRET_KEY) > 64:
    raise RuntimeError("SECRET_KEY must be less than or equal to 64 bytes.")


def base_dir(repo, relative=False):
    if relative:
        return Path(repo)
    else:
        return LFS_ROOT_REPOS / repo


def oid_path(repo, oid, relative=False):
    path = base_dir(repo,
                    relative=relative) / ".objects" / oid[0:2] / oid[2:4] / oid
    return path


def oid_upload_url(base_url, repo, oid):
    return base_url + "upload/" + repo + "/" + oid


def oid_download_url(base_url, repo, oid):
    return base_url + "download/" + repo + "/" + oid


def hash_value(data):
    h = hashlib.blake2b(digest_size=64, key=SECRET_KEY)
    h.update(data)
    return h.hexdigest()


def create_access_key(repo, req, expires_in=60 * 60):
    expires_at = int(time.time()) + expires_in
    obj = {"expires_at": expires_at, "repo": repo}
    obj_str = json.dumps(obj)
    sig = hash_value(obj_str.encode("utf-8"))
    return sig, obj_str, expires_at


def verify_access_key(key, info_str, now, repo):
    expected_key = hash_value(info_str.encode("utf-8"))
    if key != expected_key:
        return False
    try:
        info = json.loads(info_str)
    except json.JSONDecodeError:
        return False
    if info["expires_at"] < now:
        return False
    if info["repo"] != repo:
        return False
    return True


def lfs_response(obj):
    return jsonify(obj), 200, {'Content-Type': 'application/vnd.git-lfs+json'}


REPO_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")
INVALID_REPO_NAMES = [".objects"]


def check_repo(repo):
    if not all((REPO_PATTERN.match(x) and x not in INVALID_REPO_NAMES)
               for x in repo.split("/")):
        abort(400)


def download(repo, req):
    check_repo(repo)

    if "basic" not in req.get("transfers", ["basic"]):
        abort(501)

    key, info, expires_at = create_access_key(repo, req)
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
    check_repo(repo)

    if "basic" not in req.get("transfers", ["basic"]):
        abort(501)

    key, info, expires_at = create_access_key(repo, req)
    common_header = {"X-Access-Key": key, "X-Access-Info": info}
    expires_at_str = datetime.utcfromtimestamp(expires_at).isoformat() + "Z"
    base_url = request.url_root

    objects = []
    for obj in req["objects"]:
        oid = obj["oid"]
        url = oid_upload_url(base_url, repo, oid)
        size = obj["size"]
        header = {"X-File-Size": str(size)}
        header.update(common_header)
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


@app.route("/lfs/<path:repo>/info/lfs/objects/batch", methods=["POST"])
def batch(repo):
    req = request.json
    operation = req["operation"]

    if operation == "download":
        return download(repo, req)
    elif operation == "upload":
        return upload(repo, req)
    else:
        abort(400)


@app.route("/upload/<path:repo>/<oid>", methods=["PUT"])
def upload_file(repo, oid):
    body_filename = request.headers.get("X-File-Name", None)
    body_filesize = request.headers.get("X-File-Size", None)
    if not body_filename or not body_filesize:
        abort(400)

    if os.stat(body_filename).st_size != int(body_filesize):
        abort(400)

    check_repo(repo)

    path = oid_path(repo, oid)
    if path.exists():
        return "", 200

    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(body_filename, path)
    return "", 200


@app.route("/download/<path:repo>/<oid>", methods=["GET"])
def download_file(repo, oid):
    check_repo(repo)

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


FILE_ACCESS_URL_PATTERN = re.compile(r"^/(upload|download)((?:/[^/]+){3,})$")


@app.route("/auth_request")
def auth_request():
    now = time.time()
    key = request.headers.get("X-Access-Key", None)
    info = request.headers.get("X-Access-Info", None)
    original_uri = request.headers.get("X-Original-Uri", None)
    if key is None or info is None or original_uri is None:
        abort(403)

    match_data = FILE_ACCESS_URL_PATTERN.match(original_uri)
    if not match_data:
        abort(403)

    # Drop 1st "/", then split.
    repo, _ = match_data.group(2)[1:].rsplit("/", 1)
    if not verify_access_key(key, info, now, repo):
        abort(403)

    return "", 200


if __name__ == '__main__':
    port = int(os.environ["FLASK_PORT"])
    host = "localhost"
    app.run(host=host, port=port)
