import os

from taskgraph.task import *

@task_func(defaultInput="directory")
def changeDirectory(directory):
    os.chdir(directory)

@task_func
def currentDirectory():
    return os.getcwd()
