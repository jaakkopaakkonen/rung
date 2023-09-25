import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.realpath(__file__),
            "../..",
        ),
    ),
)

import taskgraph.modules

taskgraph.modules.refresh_path_executables()

taskgraph.modules.register_json_modules()