import configparser
import git
import glob
import importlib.util
import os
import pathlib
import nurmi.util


def read_external_modules():
    homedir = str(pathlib.Path.home())
    config_file = homedir + "/.nurmi/config"
    parser = configparser.ConfigParser()
    parser.read(config_file)
    repo_url = parser.get("nurmi", "external_modules")
    if repo_url:
        dest_directory = homedir + "/.nurmi/external_modules"
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
        module_name = nurmi.util.get_basename_without_ext(repo_url)
        if dest_directory[-1] != "/":
            dest_directory += "/"
        module_path = dest_directory + module_name
        return glob.glob(module_path + "/*.py")
