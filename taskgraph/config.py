import configparser
import git
import glob
import importlib.util
import os
import pathlib
import taskgraph.util


def read_external_modules():
    homedir = str(pathlib.Path.home())
    config_file = homedir + "/.taskgraph/config"
    parser = configparser.ConfigParser()
    parser.read(config_file)
    repo_url = parser.get("taskgraph", "external_modules")
    if repo_url:
        dest_directory = homedir + "/.taskgraph/external_modules"
        try:
            os.mkdir(dest_directory)
        except:
            pass
        repo = git.Git(dest_directory)
        try:
            repo.clone(repo_url)
        except git.exc.GitCommandError:
            pass
        finally:
            # Clean up repo object
            del(repo)
        module_name = taskgraph.util.get_basename_without_ext(repo_url)
        if dest_directory[-1] != "/":
            dest_directory += "/"
        module_path = dest_directory + module_name
        return glob.glob(module_path + "/*.py")
