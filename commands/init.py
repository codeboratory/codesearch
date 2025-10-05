import json
import os.path

from dataclasses import asdict
from config import default
from shared import CWD


def handle_init():
    path = f"{CWD}/codesearch.json"

    if os.path.exists(path):
        print("This repo has already been initialized")
        return

    with open(path, "w") as file:
        file.write(json.dumps(asdict(default), indent=4))
