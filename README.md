![Python Unittest](https://github.com/masamitsu-murase/gitlfs_with_nginx/workflows/Python%20Unittest/badge.svg)

# Git LFS server with nginx

Sample implementation of Git LFS server.

Core component is written in Python.  
This server uses nginx to improve performance of upload and download.

## How to use

On your server:

1. Build Docker image.  
   ```bash
   docker build -t gitlfs_with_nginx .
   ```
2. Configure `env.list`.  
   ```text
   # Specify a port of this LFS server.
   EXTERNAL_PORT=2000
   # Specify a secret key used by the LFS server.
   #  Note that the key must be less than or equal to 64 bytes.
   SECRET_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
   ```
3. [Optional] Prepare for HTTPS.  
   Set `USE_HTTPS` to `yes` in `env.list`.  
   Put server certificate and key in a directory.  
   Configure `SSL_CERTIFICATE` and `SSL_CERTIFICATE_KEY` in `env.list` to specify these file names.  
   `SSL_CERTIFICATE` and `SSL_CERTIFICATE_KEY` should not contain full path, but file name.
4. Run Docker.  
   In the following command,  `2000` corresponds to `EXTERNAL_PORT` in `env.list`.  
   You can use any directory instead of `/path/to/data` as your data directory.  
   Other parameters, such as `80` and `/opt/home/data`, must not be changed because they are used in `Dockerfile`.
   ```bash
   docker run --rm -it --env-file env.list -v /path/to/data:/opt/home/data -p2000:80 gitlfs_with_nginx
   ```
   If you enable HTTPS, use the following command.
   ```bash
   docker run --rm -it --env-file env.list -v /path/to/data:/opt/home/data -v /path/to/cert:/opt/home/ssl:ro -p2000:80 gitlfs_with_nginx
   ```
   In the above command, `/path/to/cert` is the directory where you put server certificate and key in step 3.  
   `/opt/home/ssl` must not be changed.

On your client:

1. Configure your git repository.  
   ```bash
   git config -f .lfsconfig lfs.url http://SERVER:2000/lfs/REPOSITORY_GROUP/REPOSITORY_NAME/info/lfs
   ```

## Hot to customize

### Authentication

Modify `AUTHENTICATOR` in `lfs_server.py` to specify an authenticator for Basic Authentication.

Here is very simple example.

```python
class SimpleAuthenticator(object):
    def authenticate(self, username, password, repo):
        password_dict = {
            "admin": "AdminPass",
            "user1": "UserPass"
        }
        if repo.startswith("admin"):
            if username != "admin":
                return False
        return password_dict.get(username, None) == password

AUTHENTICATOR = SimpleAuthenticator()
```


## License

This software is distibuted under the MIT License.

Copyright 2020 Masamitsu MURASE

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
