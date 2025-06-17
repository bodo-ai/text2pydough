# %%
from typing import List, Dict, Optional, Tuple
import subprocess
import logging
import os
import json
import sys

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

import os
import subprocess

def download_database(db_path):
    """Checks if the TPC-H database exists; if not, downloads it."""
    if os.path.exists(db_path):
        print("Database found, skipping download.")
    else:
        print("Database not found, downloading...")
        url = "https://github.com/lovasoa/TPCH-sqlite/releases/download/v1.0/TPC-H.db"
        try:
            subprocess.run(["wget", url, "-O", db_path], check=True)
            print("Database downloaded successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading the database: {e}")
            raise


def execute_command_str(command: List[str], cwd=None, env=None) -> str:
    """
    Executes a command and returns its corresponding string
    command: the command that will be executed
    returns: list of strings, one element of the list is equivalent to a line.
    """
    try:
        out_bytes = subprocess.check_output(command, cwd=cwd, env=env)
        out_text: str = out_bytes.decode('utf-8')
        return out_text

    except subprocess.CalledProcessError as e:
        out_bytes = e.output       # Output generated before error
        code = e.returncode   # Return code
        print("Error, executing command {} \n returned: \n {} \n code: {}"
              .format(out_bytes.decode('utf-8'), command, code))
        raise

def execute_command(command: List[str], cwd=None, env=None) -> List[str]:
    """
    Executes a command and returns a list of lines.
    command: the command that will be executed
    returns: list of strings, one element of the list is equivalent to a line.
    """
    output_string: str = execute_command_str(command, cwd, env)
    return output_string.splitlines()

def untracked_files(cwd=None) -> List[str]:
    """
    Execute git status and extract the untracked files
    """
    result: List[str] = execute_command(['git', 'status'], cwd=cwd)
    try:
        untracked_idx: int = result.index('Untracked files:')
    except ValueError:
        logger.info("No untracked files found")
        return []
    if result[0].startswith("HEAD detached"):
        raise Exception("Head detached, cannot continue please fix the HEAD.")

    untracked: List[str] = []
    i: int = untracked_idx + 3
    while i < len(result):
        if result[i].startswith('no changes added'):
            break
        if result[i].strip() == '':
            i += 1
            continue
        untracked.append(result[i].strip())
        i += 1
    return untracked


def modified_files(cwd=None) -> List[str]:
    "Execute git status and extract the modified files"
    result: List[str] = execute_command(['git', 'status'], cwd=cwd)

    modified: List[str] = []
    for line in result:
        clean_line = line.strip()
        if clean_line.startswith("modified:"):
            modified.append(clean_line.split(" ")[-1])

    return modified

# %%
def autocommit(
        cwd=None,
        message="AUTOML"
    ):
    """
    """
    try:
        result: List[str]=  execute_command(['git', 'add', '.'], cwd=cwd)
        result_commit: List[str]= execute_command(['git', 'commit', "-a", '-m', message], cwd=cwd)
    except:
        # Nothing to commit
        pass



def get_git_commit(path: str) -> Optional[str]:
    """
    Obtains the hash of the latest commit on the current branch of the git repository associated
    with the specified path, returning ``None`` if the path does not correspond to a git
    repository.
    """
    try:
        from git import Repo
    except ImportError as e:
        print(
            "Failed to import Git (the Git executable is probably not on your PATH),"
            " so Git SHA is not available. Error: %s",
            e,
        )
        return None
    try:
        if os.path.isfile(path):
            path = os.path.dirname(os.path.abspath(path))
        repo = Repo(path, search_parent_directories=True)
        if path in repo.ignored(path):
            return None
        return repo.head.commit.hexsha
    except Exception:
        return None