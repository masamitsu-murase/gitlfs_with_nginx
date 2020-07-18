import contextlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import unittest

BASE_DIR = Path(__file__).absolute().parent
GIT_BASE_DIR = BASE_DIR / "git"
GIT_REPOS_DIR = GIT_BASE_DIR / "repos"
GIT_WORKING_DIR = GIT_BASE_DIR / "working"


@contextlib.contextmanager
def cwd(new_dir):
    curdir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(curdir)


def del_rw(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


class GitLfsServerTest(unittest.TestCase):
    def setUp(self):
        if GIT_BASE_DIR.exists():
            shutil.rmtree(GIT_BASE_DIR, onerror=del_rw)

    def lfs_url(self, repo):
        return f"http://localhost:2000/lfs/{repo}/info/lfs"

    def create_git_repo(self, name):
        git_dir = GIT_REPOS_DIR / name
        git_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", ".", "--bare"], check=True, cwd=git_dir)
        return git_dir

    def clone_git_repo(self, name, dirname):
        working_dir = GIT_WORKING_DIR / dirname
        git_dir = GIT_REPOS_DIR / name
        working_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", str(git_dir), "."],
                       check=True,
                       cwd=working_dir)
        return working_dir

    def test_lfs_push(self):
        self.create_git_repo("repo1")
        repo1 = self.clone_git_repo("repo1", "repo1")
        commands = [
            ["lfs", "track", "\"*.txt\""],
            ["config", "-f", ".lfsconfig", "lfs.url",
             self.lfs_url("repo1")],
            ["add", "file1.txt", ".gitattributes", ".lfsconfig"],
            ["commit", "-m", "commit"],
            ["push", "origin", "master"],
        ]
        with (repo1 / "file1.txt").open("w") as f:
            f.write("sample")
        for command in commands:
            git_command = ["git"] + command
            subprocess.run(git_command, check=True, cwd=repo1)

        self.create_git_repo("repo2")
        repo2 = self.clone_git_repo("repo2", "repo2")
        commands = [
            ["lfs", "track", "\"*.txt\""],
            [
                "config", "-f", ".lfsconfig", "lfs.url",
                self.lfs_url("sample/repo2")
            ],
            ["add", "file1.txt", ".gitattributes", ".lfsconfig"],
            ["commit", "-m", "commit"],
            ["push", "origin", "master"],
        ]
        with (repo2 / "file1.txt").open("w") as f:
            f.write("sample")
        for command in commands:
            git_command = ["git"] + command
            subprocess.run(git_command, check=True, cwd=repo2)
