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

    def git_repo_dir(self, name):
        return GIT_REPOS_DIR / name

    def create_git_repo(self, name):
        git_dir = self.git_repo_dir(name)
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
        git_dir = self.git_repo_dir(name)
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
        rnd = random.Random(str(filepath.name))
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

    def init_lfs_and_push(self, repo_name, lfs_repo_name, dirname):
        repo = self.clone_git_repo(repo_name, dirname)
        commands = [
            ["lfs", "track", "\"*.txt\""],
            [
                "config", "-f", ".lfsconfig", "lfs.url",
                self.lfs_url(lfs_repo_name)
            ],
            ["add", ".gitattributes", ".lfsconfig"],
            ["commit", "-m", "init_lfs"],
            ["push", "origin", "master"],
        ]
        self.run_git_commands(commands, repo)

    def prepare_lfs_files(self, dirname, file_count):
        working_dir = self.working_dir(dirname)
        for i in range(file_count):
            self.create_random_file(working_dir / f"file_{i}.txt")

        file_names = [f"file_{i}.txt" for i in range(file_count)]
        unit_size = 10
        add_commands = (["add", *file_names[beg:beg + unit_size]]
                        for beg in range(0, file_count, unit_size))

        commands = [*add_commands, ["commit", "-m", "commit"]]
        self.run_git_commands(commands, working_dir)

    def push_changes(self, dirname):
        working_dir = self.working_dir(dirname)
        commands = [["push", "origin", "master"]]
        self.run_git_commands(commands, working_dir)

    def compare_dirs(self, dir1, dir2):
        dircmp = filecmp.dircmp(self.working_dir(dir1), self.working_dir(dir2))
        self.assertEqual(len(dircmp.left_only), 0)
        self.assertEqual(len(dircmp.right_only), 0)
        self.assertEqual(len(dircmp.diff_files), 0)
        self.assertEqual(len(dircmp.funny_files), 0)

    def run_lfs_simple_test(self, lfs_repo_name):
        self.create_git_repo("repo1")
        self.init_lfs_and_push("repo1", lfs_repo_name, "repo1_org")
        self.prepare_lfs_files("repo1_org", 5)
        self.push_changes("repo1_org")
        self.clone_git_repo("repo1", "repo1_clone")
        self.compare_dirs("repo1_org", "repo1_clone")

    def test_lfs_simple_test(self):
        self.run_lfs_simple_test("repo1-._Name")

    def test_lfs_simple_test_with_namespace_repo(self):
        self.run_lfs_simple_test("-/sample/.git/123/_sample_")

    def test_simultaneous_push(self):
        file_count = 20
        if "GITHUB_ACTIONS" in os.environ:
            file_count = 200

        # 3 repositories share a single LFS.
        # This is not recommended, but useful for test.
        repo_list = ["repo1", "repo2", "repo3"]
        for repo in repo_list:
            self.create_git_repo(repo)
            self.init_lfs_and_push(repo, "lfs_repo", f"{repo}_org")
            self.prepare_lfs_files(f"{repo}_org", file_count)

        process_list = []
        for repo in repo_list:
            command = ["git", "push", "origin", "master"]
            working_dir = self.working_dir(f"{repo}_org")
            proc = subprocess.Popen(command,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    cwd=working_dir)
            process_list.append(proc)
        for proc in process_list:
            proc.wait()

        process_list = []
        for repo in repo_list:
            git_dir = self.git_repo_dir(repo)
            working_dir = self.working_dir(f"{repo}_clone")
            working_dir.mkdir(parents=True, exist_ok=True)
            command = ["git", "clone", str(git_dir), "."]
            proc = subprocess.Popen(command,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    cwd=working_dir)
            process_list.append(proc)
        for proc in process_list:
            proc.wait()

        for repo in repo_list:
            self.compare_dirs(self.working_dir(f"{repo}_org"),
                              self.working_dir(f"{repo}_clone"))
