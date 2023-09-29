import configparser
import git
import glob
import importlib.util
import os
import pathlib
import taskgraph.util


def read_external_python_modules():
    """
    Reads file under user home directory ~/.taskgraph/config
    and search for
    [taskgraph]
    external_modules_python = giturl

    in that config file.
    Creates ~/.taskgraph/external_modules/python directory and clones given git url to that directory.
    Adds modules cloned from that to taskgraph
    :return: List of modules downloaded from git repo
    """

    # TODO: Implement json modules also
    # Find the config file name
    homedir = str(pathlib.Path.home())
    config_file = homedir + "/.taskgraph/config"
    if os.path.isfile(config_file) and \
       os.access(config_file, os.R_OK):
        # Parse config file name
        parser = configparser.ConfigParser()
        parser.read(config_file)
    #    try:
        repo_url = parser.get("taskgraph", "external_modules_python")
        # TODO: Add functionality to handle circumstances on updates from one side or another
        # TODO: Make sure git repo is not uselessly cloned
        if repo_url:
            # Create directory
            dest_directory = homedir + "/.taskgraph/external_modules/python"
            try:
                os.mkdir(dest_directory)
            except:
                pass
            # Clone git repo
            repo = git.Git(dest_directory)
            try:
                repo.clone(repo_url)
            except git.exc.GitCommandError:
                pass
            finally:
                # Clean up repo object
                del(repo)

            # Return all modules to be included from that directory
            module_name = taskgraph.util.get_basename_without_ext(repo_url)
            if dest_directory[-1] != "/":
                dest_directory += "/"
            module_path = dest_directory + module_name
            return glob.glob(module_path + "/*.py")
    #    except configparser.NoSectionError:
    return []
