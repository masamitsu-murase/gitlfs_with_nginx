# Git LFS server with nginx

Sample implementation of Git LFS server.

Core component is written in Python.  
This server uses nginx to improve performance of upload and download.

## How to use

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
   SECRET_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
   ```
3. Run Docker.  
   In the following command, `/opt/home/data` corresponds to `LFS_ROOT` and `2000` corresponds to `EXTERNAL_PORT`.  
   ```bash
   docker run --rm -it --env-file env.list -v /path/to/data:/opt/home/data -p2000:3000 gitlfs_with_nginx
   ```
4. Configure your git repository.  
   ```bash
   git config -f .lfsconfig lfs.url http://HOSTNAME:2000/lfs/REPOSITORY_NAME/info/lfs
   ```

