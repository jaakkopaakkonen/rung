import configparser
import git
import glob
import importlib.util
import os
import pathlib
import rung.util


def read_external_modules():
    homedir = str(pathlib.Path.home())
    config_file = homedir + "/.rung/config"
    parser = configparser.ConfigParser()
    parser.read(config_file)
    repo_url = parser.get("rung", "external_modules")
    if repo_url:
        dest_directory = homedir + "/.rung/external_modules"
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
        module_name = rung.util.get_basename_without_ext(repo_url)
        if dest_directory[-1] != "/":
            dest_directory += "/"
        module_path = dest_directory + module_name
        return glob.glob(module_path + "/*.py")
