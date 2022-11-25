import git
import logging

from rung.step import step_func, step_shell_script


log = logging.getLogger("rung")


step_shell_script(
    "cd {git_repo_path};git branch --show-current",
    "branch",
    "git_repo_path",
)


step_shell_script(
    "cd {git_repo_path};"
    " git push -o merge_request.create -o merge_request.target={target_branch} {remote} {branch}:{target_branch}",
    "push_to_gitlab",
    "git_repo_path",
    "target_branch",
    "remote",
    "branch",
)


step_shell_script(
    "cd {git_repo_path};"
    " git remote",
    "remote",
    "git_repo_path",
)
