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
   # Specify a directory to save LFS data.
   LFS_ROOT=/opt/home/data
   # Specify a port of this LFS server.
   EXTERNAL_PORT=2000
   # Specify a secret key used by the LFS server.
   #  Note that the key must be less than or equal to 64 bytes.
   SECRET_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
   ```
3. Run Docker.  
   In the following command, `/opt/home/data` corresponds to `LFS_ROOT` and `2000` corresponds to `EXTERNAL_PORT` in `env.list`.  
   ```bash
   docker run --rm -it --env-file env.list -v /path/to/data:/opt/home/data -p2000:3000 gitlfs_with_nginx
   ```

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
