import contextlib
import filecmp
import itertools
import os
from pathlib import Path
import random
import shutil
import stat
import struct
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
        subprocess.run(["git", "init", ".", "--bare"],
                       check=True,
                       cwd=git_dir,
                       stdout=subprocess.DEVNULL)
        return git_dir

    def working_dir(self, dirname):
        return GIT_WORKING_DIR / dirname

    def clone_git_repo(self, name, dirname):
        working_dir = self.working_dir(dirname)
        git_dir = GIT_REPOS_DIR / name
        working_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", str(git_dir), "."],
                       check=True,
                       cwd=working_dir,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        return working_dir

    def create_random_file(self, filepath, length=10 * 1024 * 1024):
        if length % 8 != 0:
            raise RuntimeError(
                "create_random_file can handle 8-byte aligned data only.")
        rnd = random.Random(str(filepath))
        data = (b''.join(
            map(
                struct.Struct("!Q").pack,
                map(rnd.getrandbits, itertools.repeat(64,
                                                      length // 8)))))[:length]
        with filepath.open("wb") as f:
            f.write(data)

    def run_git_commands(self, commands, cwd):
        for command in commands:
            git_command = ["git"] + command
            subprocess.run(git_command,
                           check=True,
                           cwd=cwd,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

    def exec_lfs_push(self, repo_name, lfs_repo_name):
        self.create_git_repo(repo_name)
        repo = self.clone_git_repo(repo_name, repo_name)
        commands = [
            ["lfs", "track", "\"*.txt\""],
            [
                "config", "-f", ".lfsconfig", "lfs.url",
                self.lfs_url(lfs_repo_name)
            ],
            ["add", "file1.txt", ".gitattributes", ".lfsconfig"],
            ["commit", "-m", "commit"],
            ["push", "origin", "master"],
        ]
        self.create_random_file(repo / "file1.txt")
        self.run_git_commands(commands, repo)

    def compare_dirs(self, dir1, dir2):
        dircmp = filecmp.dircmp(self.working_dir(dir1), self.working_dir(dir2))
        self.assertEqual(len(dircmp.left_only), 0)
        self.assertEqual(len(dircmp.right_only), 0)
        self.assertEqual(len(dircmp.diff_files), 0)
        self.assertEqual(len(dircmp.funny_files), 0)

    def test_lfs(self):
        self.exec_lfs_push("repo1", "repo1-._Name")
        self.clone_git_repo("repo1", "repo1_clone")
        self.compare_dirs("repo1", "repo1_clone")

        self.exec_lfs_push("repo2", "group.git/-subgroup/repo1-._Name")
        self.clone_git_repo("repo2", "repo2_clone")
        self.compare_dirs("repo2", "repo2_clone")
