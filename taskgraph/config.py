import configparser
import git
import glob
import importlib.util
import os
import pathlib
import taskgraph.util


external_module_dir = None
log_dir = None

def read_config_file():
    """
    Reads file under user home directory ~/.taskgraph/config
    and search for
    [taskgraph]
    externalModules = giturl

    in that config file.
    Creates ~/.taskgraph/externalModules/girepo directory and clones given git url to that directory.
    Adds modules cloned from that to taskgraph
    :return: List of modules downloaded from git repo
    """

    global external_module_dir
    global log_dir

    # Find the config file name
    homedir = str(pathlib.Path.home())
    config_file = homedir + "/.taskgraph/config"

    if os.path.isfile(config_file) and \
       os.access(config_file, os.R_OK):
        # Parse config file name
        parser = configparser.ConfigParser()
        parser.read(config_file)

        # Construct external_module_dir from externalModules
        try:
            repo_url = parser.get("taskgraph", "externalModules")
            # TODO: Add functionality to handle circumstances on updates from one side or another
            # TODO: Make sure git repo is not uselessly cloned
            if repo_url:
                # Create directory
                dest_directory = homedir + "/.taskgraph/externalModules"
                try:
                    os.mkdir(dest_directory)
                except:
                    pass
                # Clone git repo
                repo = git.Git(dest_directory)
                try:
                    repo.clone(repo_url)
                except git.exc.GitCommandError as gegce:
                    pass
                finally:
                    # Clean up repo object
                    del(repo)

                # Set externalModules to all modules to be included from that directory
                module_name = taskgraph.util.get_basename_without_ext(repo_url)
                if dest_directory[-1] != "/":
                    dest_directory += "/"
                external_module_dir = dest_directory + module_name
        except configparser.NoOptionError:
            pass

        # Construct log_dir from logDirectory
        try:
            log_dir = parser.get("taskgraph", "logDirectory")
        except configparser.NoOptionError:
            pass
