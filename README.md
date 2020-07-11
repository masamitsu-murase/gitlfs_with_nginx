# Git LFS server with Nginx

Sample implementation of Git LFS server.

Core component is written in Python.  
This server uses Nginx to improve performance of upload and download.

## Example

```bash
docker run --rm -it -v C:/work/git_repos/gitlfs_with_nginx:/opt/home -p2000:3000 gitlfs_with_nginx bash
```

