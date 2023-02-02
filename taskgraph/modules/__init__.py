import pathlib
import taskgraph.util

current_file = pathlib.Path(__file__)

modules = taskgraph.util.get_matching_file_basenames(
    current_file.parent,
    "*.py",
)
modules.remove(current_file.stem)

__all__ = sorted(modules)
