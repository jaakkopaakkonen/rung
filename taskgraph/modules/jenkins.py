import git
import logging

from taskgraph.task import task_func, task_shell_script


log = logging.getLogger("taskgraph")

task_shell_script(
    "curl http://{jenkins_url}/job/{job}/job/{REVISION}-{VARIANT}-{RELEASE}-build/buildWithParameters --user {username}:${apitoken} --form CLEAN_BUILD=false",
    "start_jenkins_build",
    "jenkins_url",
    "username",
    "apitoken",
    "job",
    "REVISION",
    "VARIANT",
    "RELEASE",
)
