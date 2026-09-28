import json
import os

from protection import (
    get_protected_paths,
    is_protected_path
)


os.environ[
    "AGENT_PROTECTED_PATHS"
] = json.dumps(
    [
        "tests",
        ".github"
    ]
)


print(
    "Protected Paths:"
)


print(
    get_protected_paths()
)


cases = [

    "tests/test_user.py",

    "tests/unit/test_service.py",

    "app/services/user_service.py",

    ".github/workflows/ci.yml",

    "README.md"
]


print(
    "\nPath Tests:"
)


for path in cases:

    print(
        path,
        "=>",
        is_protected_path(
            path
        )
    )